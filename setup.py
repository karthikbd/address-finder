"""
setup.py: Forces platform-specific wheel tags for address-finder.

address-finder bundles pre-compiled shared libraries (.dll/.so/.dylib),
so its wheels must be tagged with the correct platform (not 'any').
This setup.py overrides bdist_wheel.root_is_pure to accomplish that.

The build command on each platform:
  Windows:  python -m build --wheel
  Linux:    python -m build --wheel
  macOS:    python -m build --wheel

The resulting wheel filenames will use the current machine's platform tag.
For manylinux compliance on Linux, build inside a manylinux Docker container
or use auditwheel repair after building.
"""
from setuptools import setup

try:
    from wheel.bdist_wheel import bdist_wheel as _BaseBdistWheel

    class bdist_wheel(_BaseBdistWheel):
        """
        Produce a platform-specific wheel tagged py3-none-<platform>.

        address-finder is pure Python but bundles pre-compiled shared libraries,
        so wheels must carry a platform tag (not 'any') but should work with any
        Python 3.x ABI (hence 'py3' + 'none').
        """

        def finalize_options(self):
            super().finalize_options()
            # Force non-pure so setuptools emits a platform tag.
            self.root_is_pure = False

        def get_tag(self):
            _python, _abi, plat = super().get_tag()
            # Override python/abi to 'py3'/'none' — compatible with all
            # CPython and PyPy 3.x interpreters on the target platform.
            return "py3", "none", plat

except ImportError:
    bdist_wheel = None  # type: ignore[assignment,misc]


setup(
    cmdclass={"bdist_wheel": bdist_wheel} if bdist_wheel is not None else {},
)
