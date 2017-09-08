# Udacity Linux Server Configuration Project
## IP: 52.34.251.145
### Written by John Cianciolo

- This code will log you in to the server as user `grader`:
```
    ssh grader@52.34.251.145 -i ~/.ssh/linuxCourse -p 2200
```
- You will be prompted for a password, the password is `linuxCourse` (matches the file name)
# Installations and configurations
- This is the step-by-step process I took to start from a new server and end up with an app being served successfully on that server.
- Pay attention to the user who is entering code! Most code is entered as `grader` but often I am using my local computer. I indicate the name of the user as `grader$` and `ubuntu$` on the server. Code entered on my local machine will be indicated as `local$`.


##### 1. Create a Lightsail server using Amazon Web Services
- public IP address: `52.34.251.145`

##### 2. Connect using SSH in browser

##### 3. Update available package lists
    ubuntu$ sudo apt-get update
    
##### 4. Upgrade installed packages, remove old packages
    ubuntu$ sudo apt-get upgrade
    ubuntu$ sudo apt-get autoremove
    
##### 5. Create `grader` user
    ubuntu$ sudo adduser grader
- Set the password to `grader` for simplicity. 

##### 6. In Lightsail options, allow ports 2200 and 123

##### 7. Give `grader` sudo access
    ubuntu$ sudo cp /etc/sudoers.d/90-cloud-init-users /etc/sudoers.d/grader
    ubuntu$ sudo nano /etc/sudoers.d/grader
- changed `ubuntu` to `grader`

##### 8. Generate key pair for `grader` locally
    local$ ssh-keygen
- directory: `/c/Users/johnc/.ssh/linuxCourse`
- password: `linuxCourse`

##### 9. Install public key on AWS server
- Back on my server (accessed through the browser), I change user to `grader` using password `grader`
```
ubuntu$ su - grader
grader$ mkdir .ssh
grader$ touch .ssh/authorized_keys
```    

##### 10. Copy public key from local directory
    local$ cat .ssh/linuxCourse
    grader$ nano .ssh/authorized_keys
    grader$ chmod 700 .ssh
    grader$ chmod 644 .ssh/authorized_keys
    
##### 11. Install Apache
    grader$ sudo apt-get install apache2

##### 12. Install mod_wsgi
    grader$ sudo apt-get install python-setuptools libapache2-mod-wsgi
    
##### 13. Restart Apache to apply changes
    grader$ sudo service apache2 restart
    
##### 14. Configure the local time zone to UTC
- Install NTP
```
grader$ sudo apt install ntp
```
- Configuring NTP
```
grader$ sudo nano /etc/cron.daily/ntpdate
```
- Add this to the file:
> #!/bin/sh
> ntpdate ntp.ubuntu.com
- Make this new file executable:
```
grader$ sudo chmod 755 /etc/cron.daily/ntpdate
grader$ ntpdate ntpubuntu.com pool.ntp.com
```
- Check time status and confirm it worked:
```
grader$ timedatectl status
```

##### 15. Installing Postgresql
    grader$ sudo apt-get install postgresql
    
##### 16. Configuring Postgresql
- login as `postgres`
```
grader$ sudo -i -u postgres
```
- create `catalog` role
```
postgres$ createuser --interactive
```
- create database "catalog"
```
postgres$ createdb catalog
```
- create `catalog` user with password "catalog"
```
grader$ sudo adduser catalog
```
- connect to PSQL with the new `catalog` user
```
postgres$ sudo -i -u catalog
```

##### 17. Push item catalog to GitHub
```
grader$ cd /var/www
grader$ sudo mkdir DiscGolf
grader$ cd DiscGolf
grader$ sudo mkdir DiscGolf
grader$ cd DiscGolf
grader$ sudo git clone https://github.com/AdvertiseHere/DiscGolf.git
```

##### 18. Install sqlalchemy
    grader$ sudo apt-get install python-sqlalchemy
##### 19. Install python-dev
    grader$ sudo apt-get install python-dev
##### 20. Install Flask, venv, and python-pip
```
grader$ sudo apt-get install python-pip
grader$ sudo pip install virtualenv
grader$ sudo virtualenv venv
grader$ sudo chmod -R 777 venv
grader$ source venv/bin/activate
grader$ pip install Flask
grader$ python __init__.py
grader$ deactivate
```

##### 21. Configure virtual host
```
grader$ sudo nano /etc/apache2/sites-available/DiscGolf.conf
grader$ sudo a2ensite DiscGolf
grader$ sudo service apache2 reload
```

##### 22. Create the DiscGolf.wsgi file
    grader$ sudo nano /var/www/DiscGolf.wsgi
- Add this to DiscGolf.wsgi:
> <VirtualHost *:80>
  ServerName 52.34.251.145
  ServerAdmin admin@52.34.251.145
  ServerAlias ec2-52-34-251-145.us-west-2.compute.amazonaws.com
  WSGIScriptAlias / /var/www/DiscGolf/DiscGolf.wsgi
  <Directory /var/www/DiscGolf/DiscGolf/>
      Order allow,deny
      Allow from all
  </Directory>
  Alias /static /var/www/DiscGolf/DiscGolf/static
  <Directory /var/www/DiscGolf/DiscGolf/static/>
      Order allow,deny
      Allow from all
  </Directory>
  ErrorLog ${APACHE_LOG_DIR}/error.log
  LogLevel warn
  CustomLog ${APACHE_LOG_DIR}/access.log combined
</VirtualHost>

##### 23. Disable .git
    grader$ sudo nano /var/www/DiscGolf/.htaccess
- Add this to `.htaccess`:
> RedirectMatch 404 /\.git

##### 24. Install dependencies
Some of these were already installed.
```
grader$ source venv/bin/activate
grader$ sudo pip install requests
grader$ sudo pip install httplib2
grader$ sudo pip install --upgrade oauth2client
grader$ sudo pip install sqlalchemy
grader$ sudo pip install Flask-SQLAlchemy
grader$ sudo pip install python-psycopg2
```

##### 25. Configure database_setup.py and \_\_init\_\_.py
- Important: I updated the GitHub files to match these updated database_setup.py and \_\_init\_\_.py files. This step will already appear to be complete after cloning from my GitHub.
- Updated the code to postgresql from sqlite


##### 26. Import psycopg2
```
grader$ locate postgres
grader$ export PATH=/usr/share/nano/postgresql/.nanorc:"$PATH"
grader$ sudo pip install psycopg2
grader$ sudo service apache2 restart
```

##### 27. Install SQLAlchemy
- I accidentally downloaded sqlalchemy to the wrong place, so I moved it to the correct directory and deleted the old one
```
grader$ sudo rm -r /usr/lib/python2.7/dist-packages/sqlalchemy
```

##### 28. Add absolute path to client_secrets.json and fb_client_secrets.json within\_\_init\_\_.py
- Important: I updated the GitHub files to match the new \_\_init\_\_.py file. This step will already appear to be complete after cloning from my GitHub.
- Within \_\_init\_\_.py, make the following changes to all paths:
> 'fb_client_secrets.json' -----> r'/var/www/DiscGolf/DiscGolf/fb_client_secrets.json'
'client_secrets.json -----> r'/var/www/DiscGolf/DiscGolf/client_secrets.json'

##### 29. Configure Oauth to work on the AWS server
- Found my host name using [this website](http://www.info/host2ip.cgi)
```
grader$ sudo nano /etc/apache2/sites-available/DiscGolf.conf
```
- Add this line after ServerAdmin line:
> ServerAlias ec2-52-34-251-145.us-west-2.compute.amazon.com

##### 30. Add Javascript origins to Google App Engine
- Add these to authorized JavaScript origins in credentials
> http://ec2-52-34-251-145.us-west-2.compute.amazonaws.com
http://52.34.251.145

- Add this to the authorized redirect URIs:
> http://ec2-52-34-251-145.us-west-2.compute.amazonaws.com/oauth2callback

- I also enabled the Google+ API. Not sure if this was necessary.

##### 31. Add JavaScript origins and redirect URIs to client_secrets.json
- I did this in GitHub so this step will appear to be completed.

##### 32. Add valid OAuth redirect URIs to Facebook login
- same as step 30, but in Facebook app settings

##### 33. Fix syntax issues in \_\_init\_\_.py
- I fixed these issues in GitHub, which is why this step is already done.
- Removed "`\`" symbols that were causing string concactenation errors

##### 34. Rename deletemanufacturer.html and editmanufacturer.html
    grader$ cd /var/www/DiscGolf/DiscGolf/templates
    grader$ sudo mv deletemanufacturer.html deleteManufacturer.html
    grader$ sudo mv editmanufacturer.html editManufacturer.html

##### 35. Install Glances
    grader$ sudo pip install --upgrade glances
    
    
## Resources/Acknowledgements
##### Here is a list of resources used to help me complete this project:
- [Udacity Linux-based server course](https://www.udacity.com)
- [Udacity forums: Project 5 Resources](https://discussions.udacity.com/t/project-5-resources/28343)
- [Udacity forums: Facebook Auth Not Redirecting](https://discussions.udacity.com/t/facebook-auth-not-redirecting/39772/4)
- [Udacity forums: Project 5 Step 11](https://discussions.udacity.com/t/project-5-step-11/26140)
- [Udacity forums: \[Solved\] Can’t log in as grader](https://discussions.udacity.com/t/solved-cant-log-in-as-grader/249191/9)
- [Udacity forums: Tips for configuring Postgresql and Setting up Item catalog project](https://discussions.udacity.com/t/tips-for-configuring-postgresql-and-setting-up-item-catalog-project/223436)
- [Udacity forums: Deploying Item Catalog Project](https://discussions.udacity.com/t/deploying-item-catalog-project/227189)
- [Udacity forums: Ssh-keygen failing](https://discussions.udacity.com/t/ssh-keygen-failing/263885)
- [Time Synchronisation with NTP](https://help.ubuntu.com/lts/serverguide/NTP.html)
- [UbuntuTime](https://help.ubuntu.com/community/UbuntuTime)
- [archlinux: SSH keys](https://wiki.archlinux.org/index.php/SSH_keys)
- [Glances](https://pypi.python.org/pypi/Glances)
- [AWS Lightsail Documentation](https://lightsail.aws.amazon.com/ls/docs/all)
- [HTTPD - Apache2 Web Server](https://help.ubuntu.com/lts/serverguide/httpd.html)
- [DigitalOcean: How To Set Up SSH Keys](https://www.digitalocean.com/community/tutorials/how-to-set-up-ssh-keys--2)
- [DigitalOcean: How To Configure the Apache Web Server on an Ubuntu or Debian VPS](https://www.digitalocean.com/community/tutorials/how-to-configure-the-apache-web-server-on-an-ubuntu-or-debian-vps)
- [DigitalOcean: How To Secure PostgreSQL on an Ubuntu VPS](https://www.digitalocean.com/community/tutorials/how-to-secure-postgresql-on-an-ubuntu-vps)
- [DigitalOcean: How To Deploy a Flask Application on an Ubuntu VPS](https://www.digitalocean.com/community/tutorials/how-to-deploy-a-flask-application-on-an-ubuntu-vps)
- [Making a Flask app using a PostgreSQL database and deploying to Heroku](http://blog.sahildiwan.com/posts/flask-and-postgresql-app-deployed-on-heroku/)
- [Dillinger.io: Free online markdown tool](dillinger.io)
