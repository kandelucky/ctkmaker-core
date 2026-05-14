from typing import Tuple, Dict, Callable, List, Union, Optional
try:
    from PIL import Image, ImageTk, ImageColor
except ImportError:
    pass


class CTkImage:
    """
    Class to store one or two PIl.Image.Image objects and display size independent of scaling:

    light_image: PIL.Image.Image for light mode
    dark_image: PIL.Image.Image for dark mode
    size: tuple (<width>, <height>) with display size for both images
    tint_color: recolour every non-transparent pixel to this colour, keeping
        the source alpha (icon -> solid-colour silhouette). None (default)
        leaves the image untouched. A (light, dark) tuple is resolved per
        appearance mode.
    preserve_aspect: False (default) stretches the image to fill `size`.
        True scales it by the smaller side (contain-fit), centres it and
        pads the longer axis with transparent pixels (letterbox).

    One of the two images can be None and will be replaced by the other image.
    """

    _checked_PIL_import = False

    def __init__(self,
                 light_image: "Image.Image" = None,
                 dark_image: "Image.Image" = None,
                 size: Tuple[int, int] = (20, 20),
                 tint_color: Optional[Union[str, Tuple[str, str]]] = None,
                 preserve_aspect: bool = False):

        if not self._checked_PIL_import:
            self._check_pil_import()

        self._light_image = light_image
        self._dark_image = dark_image
        self._check_images()
        self._size = size
        self._tint_color = tint_color
        self._preserve_aspect = preserve_aspect

        self._configure_callback_list: List[Callable] = []
        # cache key is (scaled_size, resolved_tint_color) — preserve_aspect is
        # instance-level and the caches are dropped whenever it changes.
        self._scaled_light_photo_images: Dict[tuple, ImageTk.PhotoImage] = {}
        self._scaled_dark_photo_images: Dict[tuple, ImageTk.PhotoImage] = {}

    @classmethod
    def _check_pil_import(cls):
        try:
            _, _ = Image, ImageTk
        except NameError:
            raise ImportError("PIL.Image and PIL.ImageTk couldn't be imported")

    def add_configure_callback(self, callback: Callable):
        """ add function, that gets called when image got configured """
        self._configure_callback_list.append(callback)

    def remove_configure_callback(self, callback: Callable):
        """ remove function, that gets called when image got configured """
        self._configure_callback_list.remove(callback)

    def configure(self, **kwargs):
        if "light_image" in kwargs:
            self._light_image = kwargs.pop("light_image")
            self._scaled_light_photo_images = {}
            self._check_images()

        if "dark_image" in kwargs:
            self._dark_image = kwargs.pop("dark_image")
            self._scaled_dark_photo_images = {}
            self._check_images()

        if "size" in kwargs:
            self._size = kwargs.pop("size")

        if "tint_color" in kwargs:
            self._tint_color = kwargs.pop("tint_color")
            self._scaled_light_photo_images = {}
            self._scaled_dark_photo_images = {}

        if "preserve_aspect" in kwargs:
            self._preserve_aspect = kwargs.pop("preserve_aspect")
            self._scaled_light_photo_images = {}
            self._scaled_dark_photo_images = {}

        # call all functions registered with add_configure_callback()
        for callback in self._configure_callback_list:
            callback()

    def cget(self, attribute_name: str) -> any:
        if attribute_name == "light_image":
            return self._light_image
        elif attribute_name == "dark_image":
            return self._dark_image
        elif attribute_name == "size":
            return self._size
        elif attribute_name == "tint_color":
            return self._tint_color
        elif attribute_name == "preserve_aspect":
            return self._preserve_aspect

    def _check_images(self):
        # check types
        if self._light_image is not None and not isinstance(self._light_image, Image.Image):
            raise ValueError(f"CTkImage: light_image must be instance if PIL.Image.Image, not {type(self._light_image)}")
        if self._dark_image is not None and not isinstance(self._dark_image, Image.Image):
            raise ValueError(f"CTkImage: dark_image must be instance if PIL.Image.Image, not {type(self._dark_image)}")

        # check values
        if self._light_image is None and self._dark_image is None:
            raise ValueError("CTkImage: No image given, light_image is None and dark_image is None.")

        # check sizes
        if self._light_image is not None and self._dark_image is not None and self._light_image.size != self._dark_image.size:
            raise ValueError(f"CTkImage: light_image size {self._light_image.size} must be the same as dark_image size {self._dark_image.size}.")

    def _get_scaled_size(self, widget_scaling: float) -> Tuple[int, int]:
        return round(self._size[0] * widget_scaling), round(self._size[1] * widget_scaling)

    def _resolve_tint_color(self, appearance_mode: str) -> Optional[str]:
        """ resolve tint_color to a single colour for the given appearance
        mode, or None when no tint is set """
        if self._tint_color is None:
            return None
        if isinstance(self._tint_color, (tuple, list)):
            return self._tint_color[0] if appearance_mode == "light" else self._tint_color[1]
        return self._tint_color

    def _fit_image(self, image: "Image.Image", scaled_size: Tuple[int, int]) -> "Image.Image":
        """ resize `image` into `scaled_size`. preserve_aspect=False stretches
        to fill (legacy behaviour); True scales by the smaller side and
        centres the result on a transparent canvas (letterbox) """
        if not self._preserve_aspect:
            return image.resize(scaled_size)

        box_w, box_h = scaled_size
        native_w, native_h = image.size
        if native_w <= 0 or native_h <= 0:
            return image.resize(scaled_size)

        scale = min(box_w / native_w, box_h / native_h)
        inner_w = max(1, round(native_w * scale))
        inner_h = max(1, round(native_h * scale))
        resized = image.resize((inner_w, inner_h))

        canvas = Image.new("RGBA", (box_w, box_h), (0, 0, 0, 0))
        canvas.paste(resized, ((box_w - inner_w) // 2, (box_h - inner_h) // 2))
        return canvas

    def _tint_image(self, image: "Image.Image", tint_color: str) -> "Image.Image":
        """ replace every non-transparent pixel's RGB with `tint_color`,
        keeping the source alpha channel """
        r, g, b = ImageColor.getrgb(tint_color)[:3]
        rgba = image.convert("RGBA")
        alpha = rgba.getchannel("A")
        tinted = Image.new("RGBA", rgba.size, (r, g, b, 0))
        tinted.putalpha(alpha)
        return tinted

    def _render_photo_image(self, image: "Image.Image", scaled_size: Tuple[int, int],
                            tint_color: Optional[str]) -> "ImageTk.PhotoImage":
        rendered = self._fit_image(image, scaled_size)
        if tint_color is not None:
            rendered = self._tint_image(rendered, tint_color)
        return ImageTk.PhotoImage(rendered)

    def _get_scaled_light_photo_image(self, scaled_size: Tuple[int, int],
                                      tint_color: Optional[str]) -> "ImageTk.PhotoImage":
        cache_key = (scaled_size, tint_color)
        if cache_key in self._scaled_light_photo_images:
            return self._scaled_light_photo_images[cache_key]
        else:
            self._scaled_light_photo_images[cache_key] = self._render_photo_image(
                self._light_image, scaled_size, tint_color)
            return self._scaled_light_photo_images[cache_key]

    def _get_scaled_dark_photo_image(self, scaled_size: Tuple[int, int],
                                     tint_color: Optional[str]) -> "ImageTk.PhotoImage":
        cache_key = (scaled_size, tint_color)
        if cache_key in self._scaled_dark_photo_images:
            return self._scaled_dark_photo_images[cache_key]
        else:
            self._scaled_dark_photo_images[cache_key] = self._render_photo_image(
                self._dark_image, scaled_size, tint_color)
            return self._scaled_dark_photo_images[cache_key]

    def create_scaled_photo_image(self, widget_scaling: float, appearance_mode: str) -> "ImageTk.PhotoImage":
        scaled_size = self._get_scaled_size(widget_scaling)
        tint_color = self._resolve_tint_color(appearance_mode)

        if appearance_mode == "light" and self._light_image is not None:
            return self._get_scaled_light_photo_image(scaled_size, tint_color)
        elif appearance_mode == "light" and self._light_image is None:
            return self._get_scaled_dark_photo_image(scaled_size, tint_color)

        elif appearance_mode == "dark" and self._dark_image is not None:
            return self._get_scaled_dark_photo_image(scaled_size, tint_color)
        elif appearance_mode == "dark" and self._dark_image is None:
            return self._get_scaled_light_photo_image(scaled_size, tint_color)
