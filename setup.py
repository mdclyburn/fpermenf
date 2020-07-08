import setuptools

with open('README.md', 'r') as f:
    long_description = f.read()

setuptools.setup(
    name='fpermen-mdclyburn',
    version='0.9',
    author='Marshall Clyburn',
    author_email='mardev2013@gmail.com',
    description='Enforce file permissions',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/mdclyburn/fpermenf',
    packages='fpermenf',
    classifiers=['Programming Language :: Python :: 3',
                 'License :: OSI Approved :: BSD License',
                 'Operating System :: POSIX'],
    python_requires='>=3.7'
)
