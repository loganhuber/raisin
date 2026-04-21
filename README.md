# Raisin is a CLI tool used to compress, resize, and convert image files

## Installation:

Clone this repo, cd into it and run:

    pipx install .

## Open Image:

    raisin file.jpg -s

This opens the file in whichever default image viewer your operating system uses. It can only be used with a single file.

## Compression:
To compress an image, run:

    raisin file.jpg -c
    raisin file.jpg --compress

If you want to specify the quality, add the quality flag followed by a number between 10 and 95. Without specifying, quality is set to 20.

    raisin file.jpg -c -q 35

This compresses the image and converts it to a .webp file. To convert it to something else, specify with the format flag.

    raisin file.jpg -c -q 35 -f png

## Update default values:

WebPs suck? Quality needs to be more than 20? Both these values can be updated with the default flag.

    raisin -d -q 50
    raisin -d -f jpg

Now any image compressed with have the quality set to 50 and be converted to a jpg unless otherwise specified with the -q or -f flags.

## Recursive Flag:

To loop through a folder of images, apply the recursive flag. This creates a new folder in the same directory as the inputed folder with the suffix '_converted'.

    raisin -r mydir -c -q 30

Note: The --show flag will not work with this.

## Blur and Grayscale:

The Blur flag applies a Gaussian blur with a set radius. The Grayscale flag converts the image to black and white. Neither of these flags have adjustable values.

        raisin file.png -b
        raisin file.png -g 






