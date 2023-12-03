from setuptools import setup, find_packages

setup(
name='your_project_name',
version='1.0.0',
packages=find_packages(),
install_requires=[
'flask',
'flask-socketio',
'python-dotenv',
'requests',
'openai',
# Add other dependencies here
],
)