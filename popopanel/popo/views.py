from django.shortcuts import render
from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from django.http import HttpResponse
import logging
import subprocess
from django.contrib import messages
from django.http import HttpResponse
# from dj.models import MyTable
import os
# from dj.models import MyTable
from django.views.decorators.http import require_POST
from django.http import JsonResponse
import subprocess
from django.views.decorators.http import require_POST
from django.http import JsonResponse
logger = logging.getLogger(__name__)
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_protect

from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_protect
from popo.models import Customer , Website
import os
import subprocess
import time
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from django.views.decorators.csrf import csrf_protect
from popo.models import Website

import subprocess
import logging
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.sessions.models import Session
from django.utils import timezone
from popo.models import User
import logging
from django.shortcuts import render, get_object_or_404
from popo.models import Website

logger = logging.getLogger(__name__)

def website_info(request, id):
    website = get_object_or_404(Website, id=id)
    logger.info(f"Website: {website}")  # Check if this appears in your logs
    return render(request, 'user/website_info.html', {'website': website})\
    
def ftp_users(request, website_id):
    website = get_object_or_404(Website, id=website_id)
    if request.method == 'POST':
        ftp_username = request.POST.get('ftp_username')
        ftp_password = request.POST.get('ftp_password')
        if ftp_username and ftp_password:
            website.ftp_username = ftp_username
            website.ftp_password = ftp_password
            website.save()
            messages.success(request, 'FTP details updated successfully.')
            return redirect('ftp_users', website_id=website.id)
        else:
            messages.error(request, 'Please fill in both fields.')
    return render(request, 'user/ftp_users.html', {'website': website})

@login_required
def HomePage(request):
    user_id = request.user.id
    return render(request, 'user/home.html', {'user_id': user_id})




@login_required
def list_websites(request):
    user_id = request.user.id
    websites = Website.objects.all()
    return render(request, 'user/list_websites.html', {'websites': websites,'user_id': user_id})


@csrf_protect
@login_required
def update_website(request, website_id):
    user_id = request.user.id
    website = get_object_or_404(Website, id=website_id)

    if request.method == 'POST':
        new_website_name = request.POST.get('website_name')
        new_ftp_username = request.POST.get('ftp_username')
        new_ftp_password = request.POST.get('ftp_password')
        new_php_version = request.POST.get('php_version')

        if not (new_website_name and new_ftp_username and new_ftp_password and new_php_version):
            messages.error(request, 'Please fill out all required fields')
            return redirect('update_website', website_id=website.id)

        if not (new_website_name.endswith('.com') or new_website_name.endswith('.in')):
            messages.error(request, 'Website name must end with .com or .in')
            return redirect('update_website', website_id=website.id)

        try:
            old_ftp_username = website.ftp_username
            old_website_name = website.website_name

            if new_ftp_username != old_ftp_username:
                print(f"Renaming FTP user from {old_ftp_username} to {new_ftp_username}")

                # Check if the new username already exists
                user_check = subprocess.run(['id', new_ftp_username], capture_output=True, text=True)
                if user_check.returncode == 0:
                    messages.error(request, 'The new FTP username already exists')
                    print(f"The new FTP username {new_ftp_username} already exists")
                    return redirect('update_website', website_id=website.id)

                # Rename the user and the group
                print("Renaming the user and the group")
                subprocess.run(['sudo', 'usermod', '-l', new_ftp_username, old_ftp_username], check=True)
                subprocess.run(['sudo', 'groupmod', '-n', new_ftp_username, old_ftp_username], check=True)

                # Rename the user's home directory
                print("Renaming the user's home directory")
                subprocess.run(['sudo', 'mv', f'/home/{old_ftp_username}', f'/home/{new_ftp_username}'], check=True)

                # Adding a delay to ensure the system recognizes the new username and group
                time.sleep(2)

                # Change ownership of new home directory
                print("Changing ownership of new home directory")
                subprocess.run(['sudo', 'chown', '-R', f'{new_ftp_username}:{new_ftp_username}', f'/home/{new_ftp_username}'], check=True)

            if new_ftp_password != website.ftp_password:
                print(f"Changing password for FTP user {new_ftp_username}")
                password_change_result = change_password(new_ftp_username, new_ftp_password)
                if "Error" in password_change_result:
                    messages.error(request, password_change_result)
                    return redirect('update_website', website_id=website.id)
                else:
                    print(password_change_result)

            # Rename the website directory if the website name has changed
            if new_website_name != old_website_name:
                print(f"Renaming website directory from {old_website_name} to {new_website_name}")
                old_website_path = f'/home/{new_ftp_username}/{old_website_name}'
                new_website_path = f'/home/{new_ftp_username}/{new_website_name}'
                if os.path.exists(old_website_path):
                    subprocess.run(['sudo', 'mv', old_website_path, new_website_path], check=True)

                # Update Apache virtual host configuration
                print(f"Updating Apache virtual host configuration from {old_website_name} to {new_website_name}")
                old_apache_conf = f"/etc/apache2/sites-available/{old_website_name}.conf"
                new_apache_conf = f"/etc/apache2/sites-available/{new_website_name}.conf"

                # Move and update the Apache configuration file
                print("Moving and updating the Apache configuration file")
                subprocess.run(['sudo', 'mv', old_apache_conf, new_apache_conf], check=True)

                # Read the updated Apache configuration content
                apache_config_content = f"""
<VirtualHost *:80>
    ServerAdmin webmaster@{new_website_name}
    ServerName {new_website_name}
    DocumentRoot /home/{new_ftp_username}/{new_website_name}/public_html/
    <Directory /home/{new_ftp_username}/{new_website_name}/public_html/>
        AllowOverride all
        Require all granted
        Options FollowSymlinks
        DirectoryIndex home.html 
        Allow from all
    </Directory>
    ErrorLog /home/{new_ftp_username}/{new_website_name}/logs/error.log
    CustomLog /home/{new_ftp_username}/{new_website_name}/logs/access.log combined
</VirtualHost>
                """

                # Write the updated Apache configuration content back to file
                print("Writing the updated Apache configuration content to file")
                with open('/tmp/temp_apache_conf.conf', 'w') as file:
                    file.write(apache_config_content)
                subprocess.run(['sudo', 'mv', '/tmp/temp_apache_conf.conf', new_apache_conf], check=True)

                # Enable the new site and disable the old site
                print("Enabling the new site and disabling the old site")
                subprocess.run(['sudo', 'a2dissite', f"{old_website_name}.conf"], check=True)
                subprocess.run(['sudo', 'a2ensite', f"{new_website_name}.conf"], check=True)

                # Reload Apache
                print("Reloading Apache")
                subprocess.run(['sudo', 'systemctl', 'reload', 'apache2'], check=True)

                # Update /etc/hosts
                print(f"Updating /etc/hosts from {old_website_name} to {new_website_name}")
                update_hosts_result = update_hosts_file(old_website_name, new_website_name)
                print(update_hosts_result)
                if "Error" in update_hosts_result:
                    messages.error(request, update_hosts_result)
                    return redirect('update_website', website_id=website.id)

            # Update website details in the database
            print("Updating website details in the database")
            website.website_name = new_website_name
            website.ftp_username = new_ftp_username
            website.ftp_password = new_ftp_password
            website.php_version = new_php_version
            website.save()

            print("Website updated successfully")
            messages.success(request, 'Website updated successfully')
            return redirect('list_websites')

        except subprocess.CalledProcessError as e:
            error_message = e.stderr.decode() if e.stderr else str(e)
            print(f"Error updating website: {error_message}")
            messages.error(request, f'Error updating website: {error_message}')
            return redirect('update_website', website_id=website.id)
        except Exception as e:
            print(f"Unexpected error: {str(e)}")
            messages.error(request, f'Unexpected error: {str(e)}')
            return redirect('update_website', website_id=website.id)

    return render(request, 'user/update_website.html', {'website': website , 'user_id':user_id})


logger = logging.getLogger('django')
def update_hosts_file(old_website_name, new_website_name):
    try:
        # Read the existing content of /etc/hosts
        with open('/etc/hosts', 'r') as file:
            hosts_content = file.readlines()

        # Print original content for debugging
        print("Original /etc/hosts content:")
        for line in hosts_content:
            print(line.strip())

        # Update the content
        updated_hosts_content = []
        found = False
        for line in hosts_content:
            if old_website_name in line:
                updated_hosts_content.append(line.replace(old_website_name, new_website_name))
                found = True
                print(f"Replaced '{old_website_name}' with '{new_website_name}' in line: {line.strip()}")
            else:
                updated_hosts_content.append(line)

        if not found:
            updated_hosts_content.append(f"192.168.3.239    {new_website_name}\n")
            print(f"Added new entry for '{new_website_name}' to /etc/hosts")

        updated_hosts_content_str = ''.join(updated_hosts_content)

        # Write updated content back to /etc/hosts using sudo
        with subprocess.Popen(
            ['sudo', 'tee', '/etc/hosts'],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        ) as proc:
            stdout, stderr = proc.communicate(input=updated_hosts_content_str.encode())

            if proc.returncode != 0:
                error_message = stderr.decode() if stderr else "Unknown error"
                print(f"Failed to update /etc/hosts: {error_message}")
                logger.error(f"Failed to update /etc/hosts: {error_message}")
                return f"Error: {error_message}"

        print(f"/etc/hosts updated from {old_website_name} to {new_website_name}.")
        return f"/etc/hosts updated from {old_website_name} to {new_website_name}."
    except Exception as e:
        error_message = str(e)
        print(f"Error updating /etc/hosts: {error_message}")
        logger.error(f"Error updating /etc/hosts: {error_message}")
        return f"Error updating /etc/hosts: {error_message}"


@login_required
def delete_website(request, website_id):
    user_id = request.user.id
    website = get_object_or_404(Website, id=website_id)
    if request.method == 'POST':
        website.delete()
        messages.success(request, 'Website deleted successfully')
        return redirect('list_websites')
    return render(request, 'user/confirm_delete.html', {'website': website ,'user_id':user_id})


@csrf_protect
@login_required
def add_customer(request):
    user_id = request.user.id
    if request.method == 'POST':
        full_name = request.POST.get('full_name')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        email = request.POST.get('email')
        address1 = request.POST.get('address1')
        address2 = request.POST.get('address2')
        city = request.POST.get('city')
        country = request.POST.get('country')

        # Validate the form data
        if not (full_name and password and confirm_password and email and address1 and city and country):
            messages.error(request, 'Please fill out all required fields')
            return render(request, 'user/add_customer.html')

        if password != confirm_password:
            messages.error(request, 'Passwords do not match')
            return render(request, 'user/add_customer.html')

        # Save data to the database
        customer = Customer(
            full_name=full_name,
            password=password,
            email=email,
            address1=address1,
            address2=address2,
            city=city,
            country=country
        )
        customer.save()

        messages.success(request, 'Customer added successfully')
        return redirect('add_customer')  # Redirect to the same page after success

    return render(request, 'user/add_customer.html', {'user_id': user_id})


@csrf_protect
@login_required
def add_website(request):
    user_id = request.user.id
    if request.method == 'POST':
        customer_email = request.POST.get('customer_email')
        website_name = request.POST.get('website_name')
        ftp_username = request.POST.get('ftp_username')
        ftp_password = request.POST.get('ftp_password')
        ftp_confirm_password = request.POST.get('ftp_confirm_password')
        php_version = request.POST.get('php_version')
        database_allowed = request.POST.get('database_allowed')

        # Validate the form data
        if not (customer_email and website_name and ftp_username and ftp_password and ftp_confirm_password and php_version and database_allowed):
            messages.error(request, 'Please fill out all required fields')
            return redirect('add_website')

        if not (website_name.endswith('.com') or website_name.endswith('.in')):
            messages.error(request, 'Website name must end with .com or .in')
            return redirect('add_website')

        if ftp_password != ftp_confirm_password:
            messages.error(request, 'FTP passwords do not match')
            return redirect('add_website')

        try:
            # Create user without home directory
            create_user_command = ['sudo', 'useradd', ftp_username]
            subprocess.run(create_user_command, check=True)

            # Create necessary directories with sudo
            create_dirs_command = ['sudo',  '-u', 'root','mkdir', '-p', f'/home/{ftp_username}/{website_name}/public_html', f'/home/{ftp_username}/{website_name}/logs']
            subprocess.run(create_dirs_command, check=True)

            # Set permissions for directories and files
            set_permissions_command = ['sudo', 'chown', '-R', f'{ftp_username}:{ftp_username}', f'/home/{ftp_username}', f'/home/{ftp_username}/{website_name}']
            subprocess.run(set_permissions_command, check=True)
            subprocess.run(['sudo', 'chmod', '-R', '755', f'/home/{ftp_username}/{website_name}'], check=True)

            # Create logs files
            subprocess.run(['sudo', '-u', ftp_username, 'touch', f'/home/{ftp_username}/{website_name}/logs/error.log', f'/home/{ftp_username}/{website_name}/logs/access.log'], check=True)

            # Create index.html file using touch command
            subprocess.run(['sudo', '-u', ftp_username, 'touch', f'/home/{ftp_username}/{website_name}/public_html/home.html'], check=True)

            # Set permissions for index.html
            subprocess.run(['sudo', 'chmod', '755', f'/home/{ftp_username}/{website_name}/public_html/home.html'], check=True)

            # Modify user's shell configuration file to change directory upon login
            subprocess.run(f'sudo sh -c "echo \'cd /home/{ftp_username}/{website_name}\' >> \'/home/{ftp_username}/.bashrc\'"', shell=True, check=True)

            # Set up DNS resolution locally
            subprocess.run(f'sudo sh -c "echo \'192.168.3.239    {website_name}\' >> \'/etc/hosts\'"', shell=True, check=True)
            print(f"DNS resolution set up for domain {website_name}.")

            # Create Apache virtual host configuration
            apache_conf = f"/etc/apache2/sites-available/{website_name}.conf"
            apache_config_content = f"""
<VirtualHost *:80>
    ServerAdmin webmaster@{website_name}
    ServerName {website_name}
    DocumentRoot /home/{ftp_username}/{website_name}/public_html/
    <Directory /home/{ftp_username}/{website_name}/public_html/>
        AllowOverride all
        Require all granted
        Options FollowSymlinks
        DirectoryIndex home.html 
        Allow from all
    </Directory>
    ErrorLog /home/{ftp_username}/{website_name}/logs/error.log
    CustomLog /home/{ftp_username}/{website_name}/logs/access.log combined
</VirtualHost>
            """

            subprocess.run(f'sudo sh -c "echo \'{apache_config_content}\' > {apache_conf}"', shell=True, check=True)

            print(f"Apache virtual host configuration created: {apache_conf}")

            # Enable Apache site configuration
            enable_site_command = ['sudo', 'a2ensite', f'{website_name}.conf']
            subprocess.run(enable_site_command, check=True)
            print(f"Enabled Apache site configuration for {website_name}")

            # Reload Apache
            subprocess.run(['sudo', 'systemctl', 'reload', 'apache2'], check=True)
            print("Apache reloaded successfully.")

            customer = Customer.objects.get(email=customer_email)
        except Customer.DoesNotExist:
            messages.error(request, 'Customer not found')
            return redirect('add_website')
        except subprocess.CalledProcessError as e:
            error_message = e.stderr.decode() if e.stderr else str(e)
            messages.error(request, f'Error: {error_message}')
            return redirect('add_website')
        except Exception as e:
            messages.error(request, f'Unexpected error: {str(e)}')
            return redirect('add_website')

        # Save data to the database
        website = Website(
            customer=customer,
            website_name=website_name,
            ftp_username=ftp_username,
            ftp_password=ftp_password,
            php_version=php_version,
            database_allowed=database_allowed
        )
        website.save()

        messages.success(request, 'Website added successfully')
        return redirect('add_website')

    customers = Customer.objects.all()
    php_versions = ['7.4', '8.0', '8.1']  # Example PHP versions, you can fetch this from your model or config
    return render(request, 'user/add_website.html', {'customers': customers, 'php_versions': php_versions , 'user_id': user_id})



def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        print(f"Username: {username}")
        print(f"Entered Password: {password}")

        # Authenticate the user using the custom backend
        user = authenticate(request, username=username, password=password)

        if user is not None:
            print("Password match found, logging in user.")
            login(request, user)
            
            # Print user details to the terminal
            print(f"Authenticated User: {user.username}")
            print(f"User Email: {user.emailid}")
            print(f"User is Active: {user.is_active}")
            print(f"User is Admin: {user.is_admin}")

            return redirect('home')  # Redirect to the home page after successful login
        else:
            print("Password mismatch or user does not exist.")
            messages.error(request, 'Invalid username or password')

    return render(request, 'user/index.html')

def logout_view(request):
    # Get the current user's ID
    user_id = request.user.id

    # Print user_id for debugging
    print(f"User ID: {user_id}")

    # Invalidate all sessions for the user
    sessions = Session.objects.filter(expire_date__gte=timezone.now())
    print(sessions)
    for session in sessions:
        data = session.get_decoded()
        print(data)
        if data.get('_auth_user_id') == str(user_id):
            session.delete()

    # Log out the user
    logout(request)
    return redirect('index')



