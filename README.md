# img2shadertoy
Convert image into Shadertoy script that displays it

* Only Windows .bmp format files are supported as input. Do not use MS Paint to save images since it uses a newer unsupported header format, GIMP etc. should work.
* Redirect output to text file and paste it into Shadertoy.
* Image width must be multiple of 32. For DCT compression the image height must additionally be a multiple of 8.
* Available compression methods:
	* Run-length encoding (RLE)
	* JPEG-like Discrete Cosine Transform (DCT)

* Examples:
  * 1 bit image: https://www.shadertoy.com/view/lsVBzW
    * with RLE: https://www.shadertoy.com/view/MdGfDh
  * 4 bit image: https://www.shadertoy.com/view/4sGBzm
    * with RLE: https://www.shadertoy.com/view/XsKBDh
  * 8 bit image: https://www.shadertoy.com/view/4dyBzm
    * with DCT: https://www.shadertoy.com/view/MtycDR
