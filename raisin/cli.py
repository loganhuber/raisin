import click 
from PIL import Image
from pathlib import Path
import re
import subprocess
import platform
import json
from platformdirs import user_config_dir



CONFIG_PATH = Path(user_config_dir('raisin')) / '.config.json'

DEFAULTS = {
    "quality": 20,
    "format": "webp"
}

def load_config():
        CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)

        if not CONFIG_PATH.exists():
            save_config(DEFAULTS)
            click.echo(f"Created config at {CONFIG_PATH}")
            return DEFAULTS.copy()
    
        with open(CONFIG_PATH) as f:
            return {**DEFAULTS, **json.load(f)}
        
def save_config(config):
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=2)
 

@click.group()
@click.pass_context
def cli(ctx):
    ctx.default_map = load_config()


@click.command()
@click.argument('path', type=click.Path(exists=True, path_type=str), required=False)
@click.option('--show', '-s', is_flag=True, help="Displays the image you input. This only accepts a single file")
@click.option('--compress', '-c', is_flag=True, help="Compresses file and converts to a .WebP file unless another file type is specified with the -f flag.\nTo adjust the amount of compression, use the -q flag and specify a number between 10 and 95")
@click.option('--quality', '-q', type=click.IntRange(10, 95), help="Quality of compression. Accepts values 10 through 95")
@click.option('--resize', '-rs', type=click.IntRange(100, 2000), help="Resize the image")
@click.option('--format', '-f', help=f"This is the file type you wish to convert to.")
@click.option('--grayscale', '-g', is_flag=True, help="Converts image to black and white.")
@click.option('--recursive', '-r', is_flag=True, help="Use to convert all image files within a directory")
@click.option('--default', '-d', is_flag=True, help="Change default values")


def main(path, show, compress, quality, resize, format, grayscale, recursive, default):
    """Raisin is a CLI Tool meant to easily compress and convert image files."""

    config = load_config()

    if quality is None:
        quality = config["quality"]

    if format is None:
        format = config["format"]

    if default and path:
        click.secho("Error: -d flag can't be used with path", fg='red')
        return

    if not path:
        if default:
            update_defaults(quality, format)
            return
        else:
            click.secho("Please enter a file")
            return

    if format and not is_valid_format(format):
        click.echo(f"{format} is not a valid image format")
        return
    
    path = Path(path)

    if path.is_file(): # converts one file
        convert_file(path, show, compress, quality, resize, format, grayscale)
        click.echo("Done")

    if path.is_dir(): # converts each file in a folder
        if not recursive:
            click.secho("Error \nDirectory entered. Use '-r' flag to iterate through a folder", fg='red')
            return 
        
        if show:
            click.secho("Error: Please choose ONE file to open", fg='red')
            return

        output_folder = path.parent / f'{path.stem}-small'
        files = path.rglob("*") if recursive else path.glob("*")
        for file in files:
            # prevents from converting the same file again
            if output_folder in file.parents:
                continue

            if file.is_file() and is_valid_format(file.suffix):
                convert_file(file, show, compress, quality, format, resize, grayscale, output_folder)
                
            else:
                click.secho(f'{file.stem} was skipped because it is not an image file', fg='yellow')
        click.echo("Done")


def convert_file(file, show, compress, quality, resize, format, grayscale, output_folder=None):
    messages = []
    if show:
        show_image(file)
        return

    # check if folder exists
    if output_folder is not None:
        output_folder = Path(output_folder)
        output_folder.mkdir(parents=True, exist_ok=True)
    else:
        output_folder = file.parent

    opperations = []

    filename = Path(file).stem
    img = Image.open(file)

    save_args = {}

    if compress:
        opperations.append(('compress', lambda img: compress_img(img, quality)))

    if resize:
        opperations.append(('resize', lambda img: resize_img(img, resize)))

    if grayscale:
        opperations.append(('grayscale', lambda img: black_and_white(img)))

    suffix = get_suffixes(compress, resize, grayscale)

    new_file = output_folder / f'{filename}_{suffix}.{format}'

    for name, op in opperations:
        img, args = op(img)
        save_args.update(args)

    img.save(new_file, format=format, **save_args)

    size_info = get_size_info(file, new_file)
    messages.append((f"Saved {new_file}", 'yellow'))
    messages.append((size_info, 'green'))

    
    for message in messages:
        msg, color = message
        click.secho(msg, fg=color)
    

# ----------CONVERSIONS---------------

def compress_img(img, quality):
    return img, {"quality" : quality}

def resize_img(img, width):
    w, h = img.size
    ratio = width / w
    new_height = int(h * ratio)
    return img.resize((width, new_height)), {}

def black_and_white(img):
    return img.convert("L"), {}

# ---------END CONVERSIONS------------



def update_defaults(quality, format):
    if not is_valid_format(format):
        click.secho(f"Error: '{format}' is not a valid format", fg='red')
        return

    altered_msgs = []

    defaults = load_config()
    if defaults['quality'] == quality and defaults['format'] == format:
        click.echo("Nothing to update")
        return

    if defaults['quality'] != quality:
        old = defaults['quality']
        defaults['quality'] = quality
        msg = f"Quality updated ({old} -> {quality})"
        altered_msgs.append(msg)

    if defaults['format'] != format:
        old = defaults['format']
        defaults['format'] = format
        msg = f"Format updated ({old} -> {format})"
        altered_msgs.append(msg)
    

    save_config(defaults)
    click.secho(f"Defaults Updated:")
    for msg in altered_msgs:
        click.secho(msg, fg="green")
    

# returns whether the extention is one of Pillow's valid extensions
def is_valid_format(format):
    valid_extensions = Image.registered_extensions()
    regex = r'[^a-zA-Z0-9]'
    cleaned = re.sub(regex, '', format)
    if f".{cleaned.lower()}" in valid_extensions:
        return True
    else:
        return False
    

# --------USER INFO FOR NEW FILE--------

# returns a string to display percentage saved in compression
def get_size_info(old_file, new_file):
    old_size = old_file.stat().st_size
    new_size = new_file.stat().st_size
    percent = (1 - new_size / old_size)

    change = 'reduction'
    if old_size < new_size:
        change = 'increased'

    return f'{old_size//1024}KB -> {new_size//1024}KB ({change}: {percent:.0%})'

# returns all the suffixes for the filename
def get_suffixes(compress, resize, grayscale):
    suffixes = []
    if compress or resize:
        suffixes.append('small')
    if grayscale:
        suffixes.append('bw')

    return '_'.join(suffixes)
# ///////////////////////////////////////////////


# Pillow's native show function was causing running
# into errors when used outside the project directory
def show_image(file):
    system = platform.system()

    try:
        if system == "Darwin":      # macOS
            subprocess.run(["open", str(file)])
        elif system == "Windows":
            subprocess.run(["start", str(file)], shell=True)
        else:                       # Linux
            subprocess.run(["xdg-open", str(file)])
    except Exception as e:
        click.secho(f"Error showing image: {e}")




if __name__=='__main__':
    cli()
