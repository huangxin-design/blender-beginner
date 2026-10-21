# Publication adaptation: relative scene name and configurable installation paths.
"""CPU Open Image Denoise with an explicit working-memory target.

Use denoise(color, albedo, normal) with linear float32 RGB NumPy arrays, or run
this script on .npy arrays. OIDN internally tiles the full image, preserving
one HDR input scale across tiles. The cap excludes caller-owned image buffers.
API: https://github.com/RenderKit/oidn/blob/master/include/OpenImageDenoise/oidn.h
Parameters: https://github.com/RenderKit/oidn/blob/master/README.md
"""
import argparse
import ctypes as ct
import os
from pathlib import Path
import time

import numpy as np

DLL_FOLDER = Path(os.environ.get('OIDN_LIBRARY_DIR', 'blender.shared'))
_dll_directory = None
_library = None
_dependencies = []


def library():
    global _dll_directory, _library
    if _library is None:
        _dll_directory = os.add_dll_directory(str(DLL_FOLDER))
        # Standalone Blender Python does not preload the application's CPU plugin.
        for name in ('tbb12.dll', 'OpenImageDenoise_core.dll', 'OpenImageDenoise_device_cpu.dll'):
            _dependencies.append(ct.CDLL(str(DLL_FOLDER / name)))
        _library = ct.CDLL(str(DLL_FOLDER / 'OpenImageDenoise.dll'))
        signatures = {
            'oidnNewDevice': (ct.c_void_p, [ct.c_int]),
            'oidnSetDeviceInt': (None, [ct.c_void_p, ct.c_char_p, ct.c_int]),
            'oidnSetDeviceBool': (None, [ct.c_void_p, ct.c_char_p, ct.c_bool]),
            'oidnCommitDevice': (None, [ct.c_void_p]),
            'oidnGetDeviceError': (ct.c_int, [ct.c_void_p, ct.POINTER(ct.c_char_p)]),
            'oidnGetDeviceInt': (ct.c_int, [ct.c_void_p, ct.c_char_p]),
            'oidnReleaseDevice': (None, [ct.c_void_p]),
            'oidnNewFilter': (ct.c_void_p, [ct.c_void_p, ct.c_char_p]),
            'oidnSetSharedFilterImage': (None, [ct.c_void_p, ct.c_char_p, ct.c_void_p,
                                               ct.c_int] + [ct.c_size_t] * 5),
            'oidnSetFilterInt': (None, [ct.c_void_p, ct.c_char_p, ct.c_int]),
            'oidnSetFilterBool': (None, [ct.c_void_p, ct.c_char_p, ct.c_bool]),
            'oidnGetFilterInt': (ct.c_int, [ct.c_void_p, ct.c_char_p]),
            'oidnCommitFilter': (None, [ct.c_void_p]),
            'oidnExecuteFilter': (None, [ct.c_void_p]),
            'oidnReleaseFilter': (None, [ct.c_void_p]),
        }
        for name, (restype, argtypes) in signatures.items():
            function = getattr(_library, name)
            function.restype, function.argtypes = restype, argtypes
    return _library


def check_error(api, device, operation):
    message = ct.c_char_p()
    error = api.oidnGetDeviceError(device, ct.byref(message))
    if error:
        raise RuntimeError(f'OIDN {operation}: error {error}: '
                           f'{message.value.decode("utf-8", errors="replace")}')


def denoise(color, albedo=None, normal=None, max_memory_mb=512, threads=4, hdr=True):
    """Return denoised linear RGB; raise on any denoiser error, never return noisy fallback."""
    images = {b'color': np.ascontiguousarray(color[..., :3], dtype=np.float32)}
    if images[b'color'].ndim != 3 or images[b'color'].shape[2] != 3:
        raise ValueError('Expected an H x W x 3 RGB array')
    for name, source in ((b'albedo', albedo), (b'normal', normal)):
        if source is not None:
            images[name] = np.ascontiguousarray(source[..., :3], dtype=np.float32)
            if images[name].shape != images[b'color'].shape:
                raise ValueError('Auxiliary image dimensions must equal color dimensions')
    height, width = images[b'color'].shape[:2]
    images[b'output'] = np.empty_like(images[b'color'])
    api = library()
    device = api.oidnNewDevice(1)  # OIDN_DEVICE_TYPE_CPU
    check_error(api, device, 'device creation')
    filter_handle = None
    started = time.monotonic()
    try:
        api.oidnSetDeviceInt(device, b'numThreads', threads)
        api.oidnSetDeviceBool(device, b'setAffinity', False)
        api.oidnCommitDevice(device)
        check_error(api, device, 'device commit')
        filter_handle = api.oidnNewFilter(device, b'RT')
        check_error(api, device, 'filter creation')
        for name, data in images.items():
            api.oidnSetSharedFilterImage(filter_handle, name, data.ctypes.data, 3,
                                         width, height, 0, 12, width * 12)
        api.oidnSetFilterBool(filter_handle, b'hdr', hdr)
        api.oidnSetFilterBool(filter_handle, b'cleanAux', False)
        api.oidnSetFilterInt(filter_handle, b'quality', 6)  # OIDN_QUALITY_HIGH
        api.oidnSetFilterInt(filter_handle, b'maxMemoryMB', max_memory_mb)
        check_error(api, device, 'filter setup')
        api.oidnCommitFilter(filter_handle)
        check_error(api, device, 'filter commit')
        api.oidnExecuteFilter(filter_handle)
        check_error(api, device, 'filter execution')
        for row in range(0, height, 128):
            if not np.isfinite(images[b'output'][row:row + 128]).all():
                raise RuntimeError('OIDN returned non-finite pixels')
        print(f'OIDN_SUCCESS {width}x{height} maxMemoryMB={max_memory_mb} '
              f'seconds={time.monotonic() - started:.2f}', flush=True)
        return images[b'output']
    finally:
        if filter_handle:
            api.oidnReleaseFilter(filter_handle)
        if device:
            api.oidnReleaseDevice(device)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('color', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--albedo', type=Path)
    parser.add_argument('--normal', type=Path)
    parser.add_argument('--memory-mb', type=int, default=512)
    args = parser.parse_args()
    result = denoise(np.load(args.color, mmap_mode='r'),
                     np.load(args.albedo, mmap_mode='r') if args.albedo else None,
                     np.load(args.normal, mmap_mode='r') if args.normal else None,
                     max_memory_mb=args.memory_mb)
    np.save(args.output, result)


if __name__ == '__main__':
    main()
