# Disc Golf Catalog
This is a database that allows users to add manufacturers of disc golf discs, as well as the discs themselves. A disc golf retailer may populate this site with manufacturers and discs for easy reference and access. This app makes it simple to view a specific disc's information. This app also provides JSON endpoints for items added to the catalog.
Users can log in to this app using Google or Facebook's third-party login, allowing for safe access as well as requiring users to make a specific account for this app.

# Installation


We will be using a virtual machine (VM) to run our disc golf catalog. In order to do that, we need to install
a couple of things, including Python 2.7.xx, Vagrant, Git and Virtualbox. You may already have some of these programs.

##### Required Software
 - [VirtualBox](https://www.virtualbox.org/wiki/Downloads) - VirtualBox will run your VM.
 - [Vagrant](https://www.vagrantup.com/downloads.html) - Vagrant will link your files from your computer's documents to the cooresponding file on the VM.
- [Python 2](https://www.python.org/downloads/) - Make sure you download Python 2, not Python 3.
- [Git](https://git-scm.com/downloads) - If you're using Windows, its best to use Git Bash (included in Git) to access the VM.
- [SQLAlchemy](https://www.sqlalchemy.org/download.html) - Object-relational mapper tool that allows us to access, view, and modify our database.
- [OAuth2](https://oauth.net/2/) - OAuth is our authentication protocol. It allows for safe authentication.

You need a basic level of familiarity with the command prompt to access the catalog. There are many guides online if you have never used the command line. Here are a couple of important commands:
 - ```pwd``` returns the current directory. Enter ```pwd``` at any time if you are lost.
 - ```ls``` lists the items contained within the current directory.
 - ```cd``` will change directories. ```cd ..``` will move you up one directory level.

##### Important Files

There are a few files that power the disc golf catalog:
###### discgolf.py  - contains the Python methods that provide functionality
###### database_setup.py - contains the database schema
###### client_secrets.py/fb_client_secrets.py: provide the Google and Facebook login functionality

### Getting Started
The folder where this readme file is located is the same directory that you will be accessing your VM.
1. Go to this directory in your command prompt using ```cd```. If you list directories with ```ls```, you should see:
```
README.md           discgolf.py         database_setup.py
fb_client_secrets.py            Vagrantfile         client_secrets.py
README.md           /templates          /static
```
Remember, you want to start at the same directory as you extracted this tournament database folder to. It may be in your downloads folder if you did not specify a download path.

2. Change to the vagrant directory with ```cd vagrant```.
3. Next, enter ```vagrant up```. This command will download and install the Linux OS.
4. Once everything is installed from step 3, enter ```vagrant ssh```. This will log you in to your VM. You do not need to enter any additional information. If everything went correctly, you should see something like this:

```
$ vagrant ssh
Welcome to Ubuntu 14.04.5 LTS (GNU/Linux 3.13.0-112-generic i686)

 * Documentation:  https://help.ubuntu.com/

  System information as of Wed Mar 22 21:32:05 UTC 2017

  System load:  0.19              Processes:           82
  Usage of /:   4.2% of 39.34GB   Users logged in:     0
  Memory usage: 16%               IP address for eth0: 10.0.x.xx
  Swap usage:   0%

The shared directory is located at /vagrant
To access your shared files: cd /vagrant

Last login: Wed Mar 22 21:32:06 2017 from 10.0.x.x
vagrant@vagrant-ubuntu-trusty-32:~$
```
5. Next, enter ```cd /vagrant```. It's important to include the ```/``` before vagrant.
6. Now you are in the vagrant directory, which contains the ```discgolf``` directory. Enter ```cd discgolf``` to go there.
7. We are now in the tournament directory. It contains the files that will run our database. Enter ```ls``` and you should see:

```
discgolf.py         database_setup.py
fb_client_secrets.py            Vagrantfile         client_secrets.py
/templates          /static         README.md
```

8. The client program discgolf.py runs our disc golf catalog. Let's make sure it is running properly.
Enter ``` python dicsgolf.py``` and you should see:
```
 * Running on http://0.0.0.0:5000/
 * Restarting with reloader
```
We can terminate the connection any time by entering Control-C on the keyboard.

