from setuptools import setup, find_packages
setup(
    name="testzhuangshiqi",
    version="0.1",
    packages=find_packages(),
    scripts=['./testzhuangshiqi/zhuangshiqi.py'],

    # Project uses reStructuredText, so ensure that the docutils get
    # installed or upgraded on the target machine
    #项目打包必须具备的其他包以及版本信息
    install_requires=['docutils>=0.3'],

    package_data={
        # If any package contains *.txt or *.rst files, include them:
        '': ['*.txt', '*.rst'],
        # And include any *.msg files found in the 'hello' package, too:
        'hello': ['*.msg'],
    },

    # metadata for upload to PyPI
    author="afcentry",
    author_email="afcentry@163.com",
    description="This is an Example Package",
    license="PSF",
    keywords="testplus",
    url="http://afcentry.com",   # project home page, if any

    # could also include long_description, download_url, classifiers, etc.
)