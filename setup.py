from setuptools import setup

setup(name='weather',
      version='1.0',
      description='Returns the weather for a given date/location',
      url='http://github.com/jamietr1/weather',
      author='Jamie Todd Rubin',
      author_email='jamie@jamietoddrubin.com',
      license='MIT',
      packages=['weather'],
      package_dir={'weather': 'weather'},
      package_data={'weather': ['weather/data/*.cache']},
      install_requires=[

      ],
      scripts=['bin/weather'],
      include_package_data=True,
      zip_safe=False)
