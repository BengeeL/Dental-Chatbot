from setuptools import setup, find_packages

setup(
    name="dental-chatbot-server",
    version="1.0.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "boto3>=1.28.0",
        "chalice>=1.29.0",
        "requests>=2.28.0"
    ],
)
