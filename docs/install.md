# Installation

## PyOPF

```shell
pip install -e .
```

## ipopt

It is more recommended to use [Conda](#conda) to install Ipopt. But, if not possible, use Environment Variable approaches as explained in [Windows section](#windows).

### Conda

```shell
conda install -c conda-forge ipopt
```

### Windows

1. Download precompiled binaries of Ipopt in [Ipopt releases page](https://github.com/coin-or/Ipopt/releases). This repository is tested using [Ipopt-3.14.12-win64-msvs2019-md.zip](https://github.com/coin-or/Ipopt/releases/download/releases%2F3.14.12/Ipopt-3.14.12-win64-msvs2019-md.zip).
1. Unzip the `Ipopt-x.xx.xx-win64-msvs2019-md.zip` and move to any desired location.
1. Copy the `PATH` to `Ipopt-3.14.12-win64-msvs2019-md/bin`, for example `C:\Ipopt-3.14.12-win64-msvs2019-md\bin`.
1. Open Environment Variable. You can access it by pressing Windows-Key, type `edit the system environment variables`, and press Enter to search.
1. Click `Environment Variables`.
1. In the top area (`User variables`), double click at Variable `Path`.
1. Press `New` and paste the `PATH` to `Ipopt-3.14.12-win64-msvs2019-md/bin`.
1. Press `Ok` until `System Properties` is closed.
1. Restart (Shut down sometimes didn't work for some PC) PC.
