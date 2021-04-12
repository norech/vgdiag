# vgdiag

A simple command wrapper around valgrind that try to make it more beginner-friendly
and more readable. Experimental, but seems to work in most common cases.

## Install

`valgrind` and `python3` are required in order to run vgdiag.

```bash
git clone https://github.com/norech/vgdiag.git
cd vgdiag
chmod +x vgdiag.py
ln -s vgdiag.py /usr/local/bin/vgdiag
```

## Usage

The same arguments as valgrind can be used. See `man valgrind` for the options.

```
vgdiag [valgrind options] [your program] [your program options]
```

> Note: Stdin and stdout are redirected to the underlying process and are piped as-is.
> Stderr is readed line per line and processed by vgdiag.
