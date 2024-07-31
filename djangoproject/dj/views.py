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
from dj.models import MyTable
from django.views.decorators.http import require_POST
from django.http import JsonResponse
import subprocess
from django.views.decorators.http import require_POST
from django.http import JsonResponse


logger = logging.getLogger(__name__)

# def HomePage(request):
#     # Extract domain name from request
#     domain_name = request.get_host().split(':')[0]  # Get the domain name without port number

#     # Render the template dynamically based on the domain name
#     template_name = f"{domain_name}/home.html"
#     return render(request, 'user/home.html')

# def HomePage(request, domain_name):
#     template_name = f"{domain_name}/home.html"
#     return render(request, template_name)

def HomePage(request):
    return render(request, 'user/home.html')

from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_protect

from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_protect
from dj.models import Customer , Website

def list_websites(request):
    websites = Website.objects.all()
    return render(request, 'user/list_websites.html', {'websites': websites})

import os
import subprocess
import time
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from django.views.decorators.csrf import csrf_protect
from dj.models import Website

@csrf_protect
def update_website(request, website_id):
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

    return render(request, 'user/update_website.html', {'website': website})


def change_password(new_ftp_username, new_password):
    try:
        # Check if the user exists
        user_exists = subprocess.run(['id',new_ftp_username], check=True, capture_output=True).returncode == 0
        if not user_exists:
            return f"User {new_ftp_username} does not exist."

        # Change the user's password
        change_password_command = f'echo "{new_ftp_username}:{new_password}" | sudo chpasswd'
        subprocess.run(change_password_command, shell=True, check=True)

        return f"Password for user {new_ftp_username} has been changed."
    except subprocess.CalledProcessError as e:
        return f"Error changing password: {str(e)}"





# import os
# import subprocess
# import time
# from django.shortcuts import get_object_or_404, redirect, render
# from django.contrib import messages
# from django.views.decorators.csrf import csrf_protect
# from dj.models import Website

# @csrf_protect
# def update_website(request, website_id):
#     website = get_object_or_404(Website, id=website_id)

#     if request.method == 'POST':
#         new_website_name = request.POST.get('website_name')
#         new_ftp_username = request.POST.get('ftp_username')
#         new_ftp_password = request.POST.get('ftp_password')
#         new_php_version = request.POST.get('php_version')

#         if not (new_website_name and new_ftp_username and new_ftp_password and new_php_version):
#             messages.error(request, 'Please fill out all required fields')
#             return redirect('update_website', website_id=website.id)

#         if not (new_website_name.endswith('.com') or new_website_name.endswith('.in')):
#             messages.error(request, 'Website name must end with .com or .in')
#             return redirect('update_website', website_id=website.id)

#         try:

#             old_ftp_username = website.ftp_username
#             old_website_name = website.website_name

#             if new_ftp_username != old_ftp_username:
#                 print(f"Renaming FTP user from {old_ftp_username} to {new_ftp_username}")

#                 # Check if the new username already exists
#                 user_check = subprocess.run(['id', new_ftp_username], capture_output=True, text=True)
#                 if user_check.returncode == 0:
#                     messages.error(request, 'The new FTP username already exists')
#                     print(f"The new FTP username {new_ftp_username} already exists")
#                     return redirect('update_website', website_id=website.id)

#                 # Rename the user and the group
#                 print("Renaming the user and the group")
#                 subprocess.run(['sudo', 'usermod', '-l', new_ftp_username, old_ftp_username], check=True)
#                 subprocess.run(['sudo', 'groupmod', '-n', new_ftp_username, old_ftp_username], check=True)

#                 # Rename the user's home directory
#                 print("Renaming the user's home directory")
#                 subprocess.run(['sudo', 'mv', f'/home/{old_ftp_username}', f'/home/{new_ftp_username}'], check=True)

#                 # Adding a delay to ensure the system recognizes the new username and group
#                 time.sleep(2)

#                 # Change ownership of new home directory
#                 print("Changing ownership of new home directory")
#                 subprocess.run(['sudo', 'chown', '-R', f'{new_ftp_username}:{new_ftp_username}', f'/home/{new_ftp_username}'], check=True)

#             # Rename the website directory if the website name has changed
#             if new_website_name != old_website_name:
#                 print(f"Renaming website directory from {old_website_name} to {new_website_name}")
#                 old_website_path = f'/home/{new_ftp_username}/{old_website_name}'
#                 new_website_path = f'/home/{new_ftp_username}/{new_website_name}'
#                 if os.path.exists(old_website_path):
#                     subprocess.run(['sudo', 'mv', old_website_path, new_website_path], check=True)

#                 # Update Apache virtual host configuration
#                 print(f"Updating Apache virtual host configuration from {old_website_name} to {new_website_name}")
#                 old_apache_conf = f"/etc/apache2/sites-available/{old_website_name}.conf"
#                 new_apache_conf = f"/etc/apache2/sites-available/{new_website_name}.conf"

#                 # Move and update the Apache configuration file
#                 print("Moving and updating the Apache configuration file")
#                 subprocess.run(['sudo', 'mv', old_apache_conf, new_apache_conf], check=True)

#                 # Read the updated Apache configuration content
#                 apache_config_content = f"""
# <VirtualHost *:80>
#     ServerAdmin webmaster@{new_website_name}
#     ServerName {new_website_name}
#     DocumentRoot /home/{new_ftp_username}/{new_website_name}/public_html/
#     <Directory /home/{new_ftp_username}/{new_website_name}/public_html/>
#         AllowOverride all
#         Require all granted
#         Options FollowSymlinks
#         DirectoryIndex home.html 
#         Allow from all
#     </Directory>
#     ErrorLog /home/{new_ftp_username}/{new_website_name}/logs/error.log
#     CustomLog /home/{new_ftp_username}/{new_website_name}/logs/access.log combined
# </VirtualHost>
#                 """

#                 # Write the updated Apache configuration content back to file
#                 print("Writing the updated Apache configuration content to file")
#                 with open('/tmp/temp_apache_conf.conf', 'w') as file:
#                     file.write(apache_config_content)
#                 subprocess.run(['sudo', 'mv', '/tmp/temp_apache_conf.conf', new_apache_conf], check=True)

#                 # Enable the new site and disable the old site
#                 print("Enabling the new site and disabling the old site")
#                 subprocess.run(['sudo', 'a2dissite', f"{old_website_name}.conf"], check=True)
#                 subprocess.run(['sudo', 'a2ensite', f"{new_website_name}.conf"], check=True)

#                 # Reload Apache
#                 print("Reloading Apache")
#                 subprocess.run(['sudo', 'systemctl', 'reload', 'apache2'], check=True)

        

#                 # Update /etc/hosts
#                 print(f"Updating /etc/hosts from {old_website_name} to {new_website_name}")
#                 update_hosts_result = update_hosts_file(old_website_name, new_website_name)
#                 print(update_hosts_result)
#                 if "Error" in update_hosts_result:
#                     messages.error(request, update_hosts_result)
#                     return redirect('update_website', website_id=website.id)

#             # Update website details in the database
#             print("Updating website details in the database")
#             website.website_name = new_website_name
#             website.ftp_username = new_ftp_username
#             website.ftp_password = new_ftp_password
#             website.php_version = new_php_version
#             website.save()

#             print("Website updated successfully")
#             messages.success(request, 'Website updated successfully')
#             return redirect('list_websites')

#         except subprocess.CalledProcessError as e:
#             error_message = e.stderr.decode() if e.stderr else str(e)
#             print(f"Error updating website: {error_message}")
#             messages.error(request, f'Error updating website: {error_message}')
#             return redirect('update_website', website_id=website.id)
#         except Exception as e:
#             print(f"Unexpected error: {str(e)}")
#             messages.error(request, f'Unexpected error: {str(e)}')
#             return redirect('update_website', website_id=website.id)

#     return render(request, 'user/update_website.html', {'website': website})






import subprocess
import logging


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



# @csrf_protect
# def update_website(request, website_id):
#     website = get_object_or_404(Website, id=website_id)

#     if request.method == 'POST':
#         new_website_name = request.POST.get('website_name')
#         new_ftp_username = request.POST.get('ftp_username')
#         new_ftp_password = request.POST.get('ftp_password')
#         new_php_version = request.POST.get('php_version')

#         if not (new_website_name and new_ftp_username and new_ftp_password and new_php_version):
#             messages.error(request, 'Please fill out all required fields')
#             return redirect('update_website', website_id=website.id)

#         if not (new_website_name.endswith('.com') or new_website_name.endswith('.in')):
#             messages.error(request, 'Website name must end with .com or .in')
#             return redirect('update_website', website_id=website.id)

#         try:
#             old_ftp_username = website.ftp_username

#             if new_ftp_username != old_ftp_username:
#                 # Check if the new username already exists
#                 user_check = subprocess.run(['id', new_ftp_username], capture_output=True, text=True)
#                 if user_check.returncode == 0:
#                     messages.error(request, 'The new FTP username already exists')
#                     return redirect('update_website', website_id=website.id)

#                 # Rename the user and the group
#                 subprocess.run(['sudo', 'usermod', '-l', new_ftp_username, old_ftp_username], check=True)
#                 subprocess.run(['sudo', 'groupmod', '-n', new_ftp_username, old_ftp_username], check=True)

#                 # Rename the user's home directory
#                 subprocess.run(['sudo', 'mv', f'/home/{old_ftp_username}', f'/home/{new_ftp_username}'], check=True)

#                 # Adding a delay to ensure the system recognizes the new username and group
#                 time.sleep(2)

#                 # Change ownership of new home directory
#                 subprocess.run(['sudo', 'chown', '-R', f'{new_ftp_username}:{new_ftp_username}', f'/home/{new_ftp_username}'], check=True)

#                 # Update Apache virtual host configuration
#                 old_apache_conf = f"/etc/apache2/sites-available/{website.website_name}.conf"
#                 new_apache_conf = f"/etc/apache2/sites-available/{new_website_name}.conf"

#                 # Move and update the Apache configuration file
#                 subprocess.run(['sudo', 'mv', old_apache_conf, new_apache_conf], check=True)

#                 # Read the updated Apache configuration content
#                 apache_config_content = f"""
# <VirtualHost *:80>
#     ServerAdmin webmaster@{new_website_name}
#     ServerName {new_website_name}
#     DocumentRoot /home/{new_ftp_username}/{new_website_name}/public_html/
#     <Directory /home/{new_ftp_username}/{new_website_name}/public_html/>
#         AllowOverride all
#         Require all granted
#         Options FollowSymlinks
#         DirectoryIndex home.html 
#         Allow from all
#     </Directory>
#     ErrorLog /home/{new_ftp_username}/{new_website_name}/logs/error.log
#     CustomLog /home/{new_ftp_username}/{new_website_name}/logs/access.log combined
# </VirtualHost>
#                 """

#                 # Write the updated Apache configuration content back to file
#                 with open(new_apache_conf, 'w') as file:
#                     file.write(apache_config_content)

#                 # Enable the new site and disable the old site
#                 subprocess.run(['sudo', 'a2dissite', f"{website.website_name}.conf"], check=True)
#                 subprocess.run(['sudo', 'a2ensite', f"{new_website_name}.conf"], check=True)
#         # subprocess.run(['sudo', 'systemctl', 'reload', 'apache2'], check=True)
#                 # Reload Apache
#                 subprocess.run(['sudo', 'systemctl', 'reload', 'apache2'], check=True)

#             # Update website details in the database
#             website.website_name = new_website_name
#             website.ftp_username = new_ftp_username
#             website.ftp_password = new_ftp_password
#             website.php_version = new_php_version
#             website.save()

#             messages.success(request, 'Website updated successfully')
#             return redirect('list_websites')

#         except subprocess.CalledProcessError as e:
#             error_message = e.stderr.decode() if e.stderr else str(e)
#             messages.error(request, f'Error updating website: {error_message}')
#             return redirect('update_website', website_id=website.id)
#         except Exception as e:
#             messages.error(request, f'Unexpected error: {str(e)}')
#             return redirect('update_website', website_id=website.id)

#     return render(request, 'user/update_website.html', {'website': website})




# from django.shortcuts import render, redirect, get_object_or_404
# from django.contrib import messages
# from django.views.decorators.csrf import csrf_protect
# from dj.models import Website, Customer
# import subprocess
# import time

# @csrf_protect
# def update_website(request, website_id):
#     website = get_object_or_404(Website, id=website_id)

#     if request.method == 'POST':
#         new_website_name = request.POST.get('website_name')
#         new_ftp_username = request.POST.get('ftp_username')
#         new_ftp_password = request.POST.get('ftp_password')
#         new_php_version = request.POST.get('php_version')

#         if not (new_website_name and new_ftp_username and new_ftp_password and new_php_version):
#             messages.error(request, 'Please fill out all required fields')
#             return redirect('update_website', website_id=website.id)

#         if not (new_website_name.endswith('.com') or new_website_name.endswith('.in')):
#             messages.error(request, 'Website name must end with .com or .in')
#             return redirect('update_website', website_id=website.id)

#         try:
#             old_ftp_username = website.ftp_username

#             if new_ftp_username != old_ftp_username:
#                 # Check if the new username already exists
#                 user_check = subprocess.run(['id', new_ftp_username], capture_output=True, text=True)
#                 if user_check.returncode == 0:
#                     messages.error(request, 'The new FTP username already exists')
#                     return redirect('update_website', website_id=website.id)

#                 # Rename the user and the group
#                 subprocess.run(['sudo', 'usermod', '-l', new_ftp_username, old_ftp_username], check=True)
#                 subprocess.run(['sudo', 'groupmod', '-n', new_ftp_username, old_ftp_username], check=True)

#                 # Rename the user's home directory
#                 subprocess.run(['sudo', 'mv', f'/home/{old_ftp_username}', f'/home/{new_ftp_username}'], check=True)

#                 # Adding a delay to ensure the system recognizes the new username and group
#                 time.sleep(2)

#                 # Change ownership of new home directory
#                 subprocess.run(['sudo', 'chown', '-R', f'{new_ftp_username}:{new_ftp_username}', f'/home/{new_ftp_username}'], check=True)

#                 # Update Apache virtual host configuration
#                 # old_apache_conf = f"/etc/apache2/sites-available/{website.website_name}.conf"
#                 # new_apache_conf = f"/etc/apache2/sites-available/{new_website_name}.conf"

#                 # subprocess.run(['sudo', 'mv', old_apache_conf, new_apache_conf], check=True)
#                 # with open(new_apache_conf, 'r') as file:
#                 #     apache_config_content = file.read()

#                 # apache_config_content = apache_config_content.replace(f"/home/{old_ftp_username}", f"/home/{new_ftp_username}")

#                 # with open(new_apache_conf, 'w') as file:
#                 #     file.write(apache_config_content)

#                 # Reload Apache
#                 # subprocess.run(['sudo', 'systemctl', 'reload', 'apache2'], check=True)

#             website.website_name = new_website_name
#             website.ftp_username = new_ftp_username
#             website.ftp_password = new_ftp_password
#             website.php_version = new_php_version
#             website.save()

#             messages.success(request, 'Website updated successfully')
#             return redirect('list_websites')

#         except subprocess.CalledProcessError as e:
#             error_message = e.stderr.decode() if e.stderr else str(e)
#             messages.error(request, f'Error updating website: {error_message}')
#             return redirect('update_website', website_id=website.id)
#         except Exception as e:
#             messages.error(request, f'Unexpected error: {str(e)}')
#             return redirect('update_website', website_id=website.id)

#     return render(request, 'user/update_website.html', {'website': website})





def delete_website(request, website_id):
    website = get_object_or_404(Website, id=website_id)
    if request.method == 'POST':
        website.delete()
        messages.success(request, 'Website deleted successfully')
        return redirect('list_websites')
    return render(request, 'user/confirm_delete.html', {'website': website})


@csrf_protect
def add_customer(request):
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

    return render(request, 'user/add_customer.html')


@csrf_protect
def add_website(request):
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
    return render(request, 'user/add_website.html', {'customers': customers, 'php_versions': php_versions})



# import subprocess

# @csrf_protect
# def add_website(request):
#     if request.method == 'POST':
#         customer_email = request.POST.get('customer_email')
#         website_name = request.POST.get('website_name')
#         ftp_username = request.POST.get('ftp_username')
#         ftp_password = request.POST.get('ftp_password')
#         ftp_confirm_password = request.POST.get('ftp_confirm_password')
#         php_version = request.POST.get('php_version')
#         database_allowed = request.POST.get('database_allowed')

#         # Validate the form data
#         if not (customer_email and website_name and ftp_username and ftp_password and ftp_confirm_password and php_version and database_allowed):
#             messages.error(request, 'Please fill out all required fields')
#             return redirect('add_website')

#         if not (website_name.endswith('.com') or website_name.endswith('.in')):
#             messages.error(request, 'Website name must end with .com or .in')
#             return redirect('add_website')

#         if ftp_password != ftp_confirm_password:
#             messages.error(request, 'FTP passwords do not match')
#             return redirect('add_website')

#         try:
#             # Create user without home directory
#             create_user_command = ['sudo', 'useradd', ftp_username]
#             subprocess.run(create_user_command, check=True)

#             # Create necessary directories with sudo
#             create_dirs_command = ['sudo', '-u', 'root', 'mkdir', '-p', f'/home/{ftp_username}/{website_name}/public_html', f'/home/{ftp_username}/{website_name}/logs']
#             subprocess.run(create_dirs_command, check=True)

#             # Set permissions for directories and files
#             set_permissions_command = ['sudo', 'chown', '-R', f'{ftp_username}:{ftp_username}', f'/home/{ftp_username}', f'/home/{ftp_username}/{website_name}']
#             subprocess.run(set_permissions_command, check=True)
#             subprocess.run(['sudo', 'chmod', '-R', '755', f'/home/{ftp_username}/{website_name}'], check=True)

#             # Create logs files
#             subprocess.run(['sudo', '-u', ftp_username, 'touch', f'/home/{ftp_username}/{website_name}/logs/error.log', f'/home/{ftp_username}/{website_name}/logs/access.log'], check=True)

#             # Create index.html file using touch command
#             subprocess.run(['sudo', '-u', ftp_username, 'touch', f'/home/{ftp_username}/{website_name}/public_html/home.html'], check=True)

#             # Set permissions for index.html
#             subprocess.run(['sudo', 'chmod', '755', f'/home/{ftp_username}/{website_name}/public_html/home.html'], check=True)

#             # Modify user's shell configuration file to change directory upon login
#             subprocess.run(f'sudo sh -c "echo \'cd /home/{ftp_username}/{website_name}\' >> \'/home/{ftp_username}/.bashrc\'"', shell=True, check=True)

#             # Set up DNS resolution locally
#             subprocess.run(f'sudo sh -c "echo \'192.168.3.239    {website_name}\' >> \'/etc/hosts\'"', shell=True, check=True)
#             print(f"DNS resolution set up for domain {website_name}.")

#             # Create Apache virtual host configuration
#             apache_conf = f"/etc/apache2/sites-available/{website_name}.conf"
#             apache_config_content = f"""
# <VirtualHost *:80>
#     ServerAdmin webmaster@{website_name}
#     ServerName {website_name}
#     DocumentRoot /home/{ftp_username}/{website_name}/public_html/
#     <Directory /home/{ftp_username}/{website_name}/public_html/>
#         AllowOverride all
#         Require all granted
#         Options FollowSymlinks
#         DirectoryIndex home.html 
#         Allow from all
#     </Directory>
#     ErrorLog /home/{ftp_username}/{website_name}/logs/error.log
#     CustomLog /home/{ftp_username}/{website_name}/logs/access.log combined
# </VirtualHost>
#             """

#             subprocess.run(f'sudo sh -c "echo \'{apache_config_content}\' > {apache_conf}"', shell=True, check=True)

#             print(f"Apache virtual host configuration created: {apache_conf}")
#             # Write virtual host configuration to file using sudo
#             # with open(apache_conf, 'w') as file:
#             #     file.write(apache_config_content)

#             # print(f"Apache virtual host configuration created: {apache_conf}")
            

#             # Enable Apache site configuration
#             enable_site_command = ['sudo', 'a2ensite', f'{website_name}.conf']
#             subprocess.run(enable_site_command, check=True)
#             print(f"Enabled Apache site configuration for {website_name}")

#             # Reload Apache
#             subprocess.run(['sudo', 'systemctl', 'reload', 'apache2'], check=True)
#             print("Apache reloaded successfully.")

#             customer = Customer.objects.get(email=customer_email)
#         except Customer.DoesNotExist:
#             messages.error(request, 'Customer not found')
#             return redirect('add_website')
#         except subprocess.CalledProcessError as e:
#             error_message = e.stderr.decode() if e.stderr else str(e)
#             messages.error(request, f'Error: {error_message}')
#             return redirect('add_website')
#         except Exception as e:
#             messages.error(request, f'Unexpected error: {str(e)}')
#             return redirect('add_website')

#         # Save data to the database
#         website = Website(
#             customer=customer,
#             website_name=website_name,
#             ftp_username=ftp_username,
#             ftp_password=ftp_password,
#             php_version=php_version,
#             database_allowed=database_allowed
#         )
#         website.save()

#         messages.success(request, 'Website added successfully')
#         return redirect('add_website')

#     customers = Customer.objects.all()
#     php_versions = ['7.4', '8.0', '8.1']  # Example PHP versions, you can fetch this from your model or config
#     return render(request, 'user/add_website.html', {'customers': customers, 'php_versions': php_versions})




# def EditPage(request):
#     return render(request, 'user/edit.html')

# from django.shortcuts import render, get_object_or_404, redirect
# from django.shortcuts import render, get_object_or_404, redirect
# from django.contrib import messages
# from dj.models import MyTable

# def EditPage(request, user_id):
#     user = get_object_or_404(MyTable, id=user_id)
    
#     if request.method == 'POST':
#         uname = request.POST.get('username').strip()
#         email = request.POST.get('email')
#         pass1 = request.POST.get('password')
#         domain_name = request.POST.get('domain_name')
        
#         # Perform validations
#         if not domain_name.endswith('.com'):
#             messages.error(request, 'Domain name must end with .com')
#         else:
#             # Update user details
#             user.username = uname
#             user.email = email
#             user.password = pass1
#             user.domain_name = domain_name
#             user.save()
#             messages.success(request, 'User details updated successfully.')
#             return redirect('user_detail', user_id=user.id)  # Redirect to user detail page

#     return render(request, 'user/edit.html', {'user': user})

# def user_detail(request, user_id):
#     user = get_object_or_404(MyTable, id=user_id)
#     return render(request, 'user/user_detail.html', {'user': user})


def dashboard(request):
    # Retrieve list of domains and corresponding users
    domains_users = []
    
    return render(request, 'user/dashboard.html', {'domains_users': domains_users})


def delete_user(request):
    users = User.objects.all()
    return render(request, 'user/deleteuser.html', {'users': users})


def delete_user_process(request):
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        try:
            user = User.objects.get(pk=user_id)
            username = user.username

            user.delete()
        
            subprocess.run(['sudo', 'userdel', '-r', username])
    
            messages.success(request, f"User '{username}' deleted successfully.")

        except User.DoesNotExist:
           
            messages.error(request, "User not found.")

        except Exception as e:
            
            messages.error(request, f"An error occurred: {str(e)}")
    
    return redirect('delete_user')  


from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
import subprocess
from .models import MyTable

def SignupPage(request):
    if request.method == 'POST':
        uname = request.POST.get('username').strip()
        email = request.POST.get('email')
        pass1 = request.POST.get('password')
        confirm_pass1 = request.POST.get('confirm_password')
        domain_name = request.POST.get('domain_name')
        php_version = request.POST.get('php_version')

        if not domain_name.endswith('.com'):
            messages.error(request, 'Domain name must end with .com')
            return redirect('index')

        if pass1 != confirm_pass1:
            messages.error(request, 'Passwords do not match')
            return redirect('index')

        try:
            # Create user without home directory
            create_user_command = ['sudo', 'useradd', uname]
            subprocess.run(create_user_command, check=True)

            # Create necessary directories with sudo
            create_dirs_command = ['sudo', '-u', 'root', 'mkdir', '-p', f'/home/{uname}/{domain_name}/public_html', f'/home/{uname}/{domain_name}/logs']
            subprocess.run(create_dirs_command, check=True)

            # Set permissions for directories and files
            set_permissions_command = ['sudo', 'chown', '-R', f'{uname}:{uname}', f'/home/{uname}/{domain_name}']
            subprocess.run(set_permissions_command, check=True)
            subprocess.run(['sudo', 'chmod', '-R', '755', f'/home/{uname}/{domain_name}'], check=True)

            # Create logs files
            subprocess.run(['sudo', '-u', uname, 'touch', f'/home/{uname}/{domain_name}/logs/error.log', f'/home/{uname}/{domain_name}/logs/access.log'], check=True)

            # Create index.html file using touch command
            subprocess.run(['sudo', '-u', uname, 'touch', f'/home/{uname}/{domain_name}/public_html/home.html'], check=True)

            # Set permissions for index.html
            subprocess.run(['sudo', 'chmod', '755', f'/home/{uname}/{domain_name}/public_html/home.html'], check=True)

            # Modify user's shell configuration file to change directory upon login
            subprocess.run(f'sudo sh -c "echo \'cd /home/{uname}/{domain_name}\' >> \'/home/{uname}/.bashrc\'"', shell=True, check=True)

            # Set up DNS resolution locally
            subprocess.run(f'sudo sh -c "echo \'192.168.3.239    {domain_name}\' >> \'/etc/hosts\'"', shell=True, check=True)
            print(f"DNS resolution set up for domain {domain_name}.")

            # Create Apache virtual host configuration
            apache_conf = f"/etc/apache2/sites-available/{domain_name}.conf"
            apache_config_content = f"""
<VirtualHost *:80>
    ServerAdmin webmaster@{domain_name}
    ServerName {domain_name}
    DocumentRoot /home/{uname}/{domain_name}/public_html/
    <Directory /home/{uname}/{domain_name}/public_html/>
        AllowOverride all
        Require all granted
        Options FollowSymlinks
        DirectoryIndex home.html 
        Allow from all
    </Directory>
    ErrorLog /home/{uname}/{domain_name}/logs/error.log
    CustomLog /home/{uname}/{domain_name}/logs/access.log combined
</VirtualHost>
            """
            # Write virtual host configuration to file using sudo
            subprocess.run(f'sudo sh -c "echo \'{apache_config_content}\' > {apache_conf}"', shell=True, check=True)

            print(f"Apache virtual host configuration created: {apache_conf}")

            # Enable Apache site configuration
            enable_site_command = ['sudo', 'a2ensite', f'{domain_name}.conf']
            subprocess.run(enable_site_command, check=True)
            print(f"Enabled Apache site configuration for {domain_name}")

            
            apache_status = subprocess.run(['systemctl', 'is-active', 'apache2'], capture_output=True, text=True)
            if apache_status.stdout.strip() == 'active':
                
                subprocess.run(['sudo', 'systemctl', 'reload', 'apache2'], check=True)
                print("Apache reloaded successfully.")
            else:
                print("Apache service is not active, cannot reload.")

            user_path = f"/home/{uname}/php"
            os.makedirs(user_path, exist_ok=True)
            if not download_and_install_php(user_path, php_version):
                messages.error(request, f"Failed to install PHP {php_version}.")
                return redirect('index')

            # Save user details to the database
            MyTable.objects.create(username=uname, email=email, password=pass1, domain_name=domain_name, php_version=php_version)

            

            messages.success(request, 'User created successfully. Please login.')
            return redirect('login')
        
        except subprocess.CalledProcessError as e:
            error_message = f'Error: {e.returncode}, Output: {e.output.decode() if e.output else ""}'
            messages.error(request, error_message)
            return redirect('index')
        
        except Exception as e:
            error_message = f'Error creating user: {str(e)}'
            messages.error(request, error_message)
            return redirect('index')

    users = MyTable.objects.all()
    return render(request, 'user/index.html', {'users': users})



def update_php_version(user_path, php_version):
    # This is a placeholder function, replace with actual commands to download and install PHP
    try:
        # Construct the download URL and file paths
        download_url = f"https://www.php.net/distributions/php-{php_version}.tar.gz"
        tarball_path = os.path.join(user_path, f"php-{php_version}.tar.gz")
        extract_path = os.path.join(user_path, f"php-{php_version}")

        # Download the PHP version
        subprocess.run(["wget", download_url, "-O", tarball_path], check=True)

        # Extract the tarball
        subprocess.run(["tar", "-xzf", tarball_path, "-C", user_path], check=True)

        # Navigate to the extracted directory and install PHP
        os.chdir(extract_path)
        subprocess.run(["./configure", f"--prefix={user_path}"], check=True)
        subprocess.run(["make"], check=True)
        subprocess.run(["make", "install"], check=True)

        return True
    except subprocess.CalledProcessError as e:
        print(f"Error occurred while downloading/installing PHP: {e}")
        return False




from django.shortcuts import render, get_object_or_404
from dj.models import MyTable

# def EditUser(request):

#     data = MyTable.objects.all()

#     if request.method == "POST":
#         user_id = request.POST.get('user_id')
#         user = get_object_or_404(MyTable, id=user_id)
#         user.username = request.POST.get('username')
#         user.email = request.POST.get('email')
#         user.domain_name = request.POST.get('domain_name')
#         user.php_version = request.POST.get('php_version')
#         user.save()
    
#     print(data)
#     return render(request, 'user/edit_user.html', {'us': data})

# def EditUser(request):
#     users = MyTable.objects.all()
#     print(users)  # Debug: Check if users queryset is populated correctly
#     return render(request, 'user/edit_user.html', {'users': users})

# def EditUser(request):
#     if request.method == 'POST':
#         user_id = request.POST.get('user_id')
#         uname = request.POST.get('username')
#         email = request.POST.get('email')
#         domain_name = request.POST.get('domain_name')
#         php_version = request.POST.get('php_version')

#         try:
#             user = MyTable.objects.get(id=user_id)
#             user.username = uname
#             user.email = email
#             user.domain_name = domain_name
#             user.php_version = php_version
#             user.save()
#             messages.success(request, 'User details updated successfully.')
#             return redirect('edit_user')
#         except MyTable.DoesNotExist:
#             messages.error(request, 'User not found.')
#         except Exception as e:
#             messages.error(request, f'Error updating user: {str(e)}')

#     # Fetch all users from the database
#     users = MyTable.objects.all()
#     return render(request, 'user/edit_user.html', {'users': users})
# def EditUserPage(request, user_id):
#     user = get_object_or_404(MyTable, id=user_id)
#     if request.method == 'POST':
#         user.username = request.POST.get('username').strip()
#         user.email = request.POST.get('email')
#         user.password = request.POST.get('password')
#         user.domain_name = request.POST.get('domain_name')
#         user.php_version = request.POST.get('php_version')
#         user.save()
#         messages.success(request, 'User details updated successfully.')
#         return redirect('index')

#     return render(request, 'user/edit_user.html', {'user': user})

# @require_POST
# def update_user(request):
#     user_id = request.POST.get('user_id')
#     username = request.POST.get('username')
#     email = request.POST.get('email')
#     domain_name = request.POST.get('domain_name')
#     php_version = request.POST.get('php_version')

#     try:
#         user = MyTable.objects.get(id=user_id)
#         user.username = username
#         user.email = email
#         user.domain_name = domain_name
#         user.php_version = php_version
#         user.save()

#         return JsonResponse({'success': True})
#     except MyTable.DoesNotExist:
#         return JsonResponse({'error': 'User not found'}, status=404)

# @require_POST
# def update_user(request):
#     user_id = request.POST.get('user_id')
#     username = request.POST.get('username')
#     email = request.POST.get('email')
#     domain_name = request.POST.get('domain_name')
#     php_version = request.POST.get('php_version')
#     new_password = request.POST.get('new_password')
#     confirm_password = request.POST.get('confirm_password')

#     if new_password and new_password != confirm_password:
#         return JsonResponse({'error': 'New Password and Confirm Password do not match.'}, status=400)


#     try:
#         user = MyTable.objects.get(id=user_id)
#         old_username = user.username
#         new_username = username

#         # Update user in database
#         user.username = username
#         user.email = email
#         user.domain_name = domain_name
#         user.php_version = php_version

#         if new_password:
#             user.password = new_password  # Assuming password is stored as plain text, not recommended
#         user.save()

#         # Rename user on the server
#         rename_result = rename_user(old_username, new_username)
#         if "Error" in rename_result:
#             return JsonResponse({'error': rename_result}, status=500)

#         if new_password:
#             password_change_result = change_password(new_username, new_password)
#             if "Error" in password_change_result:
#                 return JsonResponse({'error': password_change_result}, status=500)

#         # Update Apache configuration
#         apache_result = update_apache_config(old_username, new_username,domain_name)
#         if "Error" in apache_result:
#             return JsonResponse({'error': apache_result}, status=500)

#         return JsonResponse({'success': True, 'rename_result': rename_result, 'apache_result': apache_result})
#     except MyTable.DoesNotExist:
#         return JsonResponse({'error': 'User not found'}, status=404)
#     except subprocess.CalledProcessError as e:
#         return JsonResponse({'error': f'Error updating user on server: {e}'}, status=500)
#     except Exception as e:
#         return JsonResponse({'error': f'Error updating user: {str(e)}'}, status=500)

@require_POST
def update_user(request):
    user_id = request.POST.get('user_id')
    username = request.POST.get('username')
    email = request.POST.get('email')
    domain_name = request.POST.get('domain_name')
    php_version = request.POST.get('php_version')
    new_password = request.POST.get('new_password')
    confirm_password = request.POST.get('confirm_password')

    if new_password and new_password != confirm_password:
        return JsonResponse({'error': 'New Password and Confirm Password do not match.'}, status=400)

    try:
        user = MyTable.objects.get(id=user_id)
        old_username = user.username
        old_domain_name = user.domain_name
        new_username = username
        new_domain_name = domain_name

        # Update user in database
        user.username = username
        user.email = email
        user.domain_name = domain_name
        user.php_version = php_version

        if new_password:
            user.password = new_password  # Assuming password is stored as plain text, not recommended
        user.save()

        # Rename user on the server
        rename_result = rename_user(old_username, new_username)
        if "Error" in rename_result:
            return JsonResponse({'error': rename_result}, status=500)

        if new_password:
            password_change_result = change_password(new_username, new_password)
            if "Error" in password_change_result:
                return JsonResponse({'error': password_change_result}, status=500)

        # Update Apache configuration and domain directory
        apache_result = update_apache_config(old_username, new_username, old_domain_name, new_domain_name)
        if "Error" in apache_result:
            return JsonResponse({'error': apache_result}, status=500)

        return JsonResponse({'success': True, 'rename_result': rename_result, 'apache_result': apache_result})
    except MyTable.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)
    except subprocess.CalledProcessError as e:
        return JsonResponse({'error': f'Error updating user on server: {e}'}, status=500)
    except Exception as e:
        return JsonResponse({'error': f'Error updating user: {str(e)}'}, status=500)



def get_user_details(request, user_id):
    try:
        user = MyTable.objects.get(id=user_id)
        data = {
            'username': user.username,
            'email': user.email,
            'domain_name': user.domain_name,
            'php_version': user.php_version,
            'password': user.password
        }
        return JsonResponse(data)
    except MyTable.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)

def EditUser(request):
    datas = MyTable.objects.all()
    print(datas)
    return render(request, 'user/edit_user.html', {'datas': datas})


# def change_password(username, new_password):
#     try:
#         # Check if the user exists
#         user_exists = subprocess.run(['id', username], check=True, capture_output=True).returncode == 0
#         if not user_exists:
#             return f"User {username} does not exist."

#         # Change the user's password
#         change_password_command = f'echo "{username}:{new_password}" | sudo chpasswd'
#         subprocess.run(change_password_command, shell=True, check=True)

#         return f"Password for user {username} has been changed."
#     except subprocess.CalledProcessError as e:
#         return f"Error changing password: {str(e)}"



def rename_user(old_username, new_username):
    try:
        # Check if the old user exists
        if subprocess.run(['id', old_username], check=True, capture_output=True).returncode != 0:
            return f"User {old_username} does not exist."

        # Check if the new user already exists
        if subprocess.run(['id', new_username], capture_output=True).returncode == 0 and old_username != new_username:
            return f"User {new_username} already exists."

        # Rename the user
        subprocess.run(['sudo', 'usermod', '-l', new_username, old_username], check=True)

        # Rename the home directory
        old_home_dir = f"/home/{old_username}"
        new_home_dir = f"/home/{new_username}"
        subprocess.run(['sudo', 'usermod', '-d', new_home_dir, '-m', new_username], check=True)

        # Rename the user's group
        subprocess.run(['sudo', 'groupmod', '-n', new_username, old_username], check=True)

        # Update ownership of all files in the new home directory
        subprocess.run(['sudo', 'chown', '-R', f'{new_username}:{new_username}', new_home_dir], check=True)

        return f"User {old_username} has been renamed to {new_username}."
    except subprocess.CalledProcessError as e:
        return f"Error renaming user: {str(e)}"


logger = logging.getLogger('django')




import os
import subprocess
import logging

logger = logging.getLogger('django')

def update_apache_config(old_username, new_username, old_domain_name, new_domain_name):
    try:
        logger.debug(f"Old username: {old_username}")
        logger.debug(f"New username: {new_username}")
        logger.debug(f"Old domain name: {old_domain_name}")
        logger.debug(f"New domain name: {new_domain_name}")

        config_dir = '/etc/apache2/sites-available'
        old_conf_path = os.path.join(config_dir, f"{old_domain_name}.conf")
        new_conf_path = os.path.join(config_dir, f"{new_domain_name}.conf")

        # Check if the old configuration file exists
        if not os.path.exists(old_conf_path):
            logger.error(f"Old config file {old_conf_path} does not exist.")
            return f"Error: Old config file {old_conf_path} does not exist."

        # Rename the old configuration file to the new domain name
        if old_conf_path != new_conf_path:
            subprocess.run(['sudo', 'mv', old_conf_path, new_conf_path], check=True)
        else:
            logger.warning("Source and destination paths are the same. Skipping move operation.")

        # Update the configuration content
        content = f"""
<VirtualHost *:80>
    ServerAdmin webmaster@{new_domain_name}
    ServerName {new_domain_name}
    DocumentRoot /home/{new_username}/{new_domain_name}/public_html/
    <Directory /home/{new_username}/{new_domain_name}/public_html/>
        AllowOverride all
        Require all granted
        Options FollowSymlinks
        DirectoryIndex home.html 
        Allow from all
    </Directory>
    ErrorLog /home/{new_username}/{new_domain_name}/logs/error.log
    CustomLog /home/{new_username}/{new_domain_name}/logs/access.log combined
</VirtualHost>
        """

        # Write the new configuration to the new conf file
        sudo_command = ['sudo', 'tee', new_conf_path]
        with subprocess.Popen(sudo_command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE) as proc:
            stdout, stderr = proc.communicate(input=content.encode())

            if proc.returncode != 0:
                logger.error(f"Failed to write Apache config: {stderr.decode()}")
                return f"Error: {stderr.decode()}"

        # Enable the new site and disable the old site
        subprocess.run(['sudo', 'a2dissite', f"{old_domain_name}.conf"], check=True)
        subprocess.run(['sudo', 'a2ensite', f"{new_domain_name}.conf"], check=True)
        # subprocess.run(['sudo', 'systemctl', 'reload', 'apache2'], check=True)

        # Rename the domain directory if necessary
        old_domain_dir = f"/home/{new_username}/{old_domain_name}"
        new_domain_dir = f"/home/{new_username}/{new_domain_name}"
        
        if old_domain_dir != new_domain_dir:
            if os.path.exists(old_domain_dir):
                if os.path.exists(new_domain_dir):
                    logger.error(f"New domain directory {new_domain_dir} already exists.")
                    return f"Error: New domain directory {new_domain_dir} already exists."
                subprocess.run(['sudo', 'mv', old_domain_dir, new_domain_dir], check=True)
            else:
                logger.error(f"Old domain directory {old_domain_dir} does not exist.")
                return f"Error: Old domain directory {old_domain_dir} does not exist."

        # Update ownership of the new domain directory
        subprocess.run(['sudo', 'chown', '-R', f'{new_username}:{new_username}', new_domain_dir], check=True)

        

        hosts_result = update_hosts_file(old_domain_name, new_domain_name)
        if "Error" in hosts_result:
            return JsonResponse({'error': hosts_result}, status=500)

        return f"Apache configuration and directory updated from {old_domain_name} to {new_domain_name}."
    except subprocess.CalledProcessError as e:
        logger.error(f"Error updating Apache config: {e}")
        return f"Error updating Apache config: {str(e)}"
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return f"Error: {str(e)}"



        print(f"Error configuring virtual host: {e}")
        raise





# def update_php_version(username, php_version):
#     try:
#         # Create user's PHP directory if it doesn't exist
#         user_php_dir = f"/home/{username}/php/{php_version}"
#         if not os.path.exists(user_php_dir):
#             subprocess.run(['sudo', '-u', 'root', 'mkdir', '-p', user_php_dir], check=True)

#         # Ensure the required repository is added
#         add_repo_command = 'sudo add-apt-repository ppa:ondrej/php -y'
#         subprocess.run(add_repo_command, shell=True, check=True)

#         # Update the package list
#         subprocess.run(['sudo', 'apt-get', 'update'], check=True)

#         # Correct PHP package name
#         php_package = f'php{php_version}'

#         # Install PHP version using apt-get if not already installed
#         php_path = f"/usr/bin/php{php_version}"
#         if not os.path.isfile(php_path):
#             install_php_command = ['sudo', 'apt-get', 'install', '-y', php_package]
#             subprocess.run(install_php_command, check=True)

#         # Link PHP binary in the user's PHP directory
#         subprocess.run(['sudo', '-u', 'root', 'ln', '-s', php_path, f'{user_php_dir}/php'], check=True)

#         # Store PHP version in a user-specific file
#         php_version_file = f"{user_php_dir}/php_version"
#         with open(php_version_file, 'w') as f:
#             f.write(php_version)

#         print(f"PHP version {php_version} installed for user {username}.")

#     except subprocess.CalledProcessError as e:
#         raise Exception(f'Error installing PHP version: {e.returncode}, Output: {e.output.decode() if e.output else ""}')

#     except Exception as e:
#         raise Exception(f'Error installing PHP or creating directories: {str(e)}')



# import subprocess
# import shutil
# import glob
# import logging

# logger = logging.getLogger('django')

# def update_domain(old_domain, new_domain):
#     old_conf = f"/etc/apache2/sites-available/{old_domain}.conf"
#     new_conf = f"/etc/apache2/sites-available/{new_domain}.conf"

#     if not os.path.isfile(old_conf):
#         return f"Configuration file for {old_domain} does not exist."

#     try:
#         # Copy the old configuration to the new configuration file
#         shutil.copyfile(old_conf, new_conf)

#         # Update the domain name inside the configuration file
#         with open(new_conf, 'r') as file:
#             filedata = file.read()

#         filedata = filedata.replace(old_domain, new_domain)

#         with open(new_conf, 'w') as file:
#             file.write(filedata)

#         # Disable the old site and enable the new site
#         subprocess.run(['sudo', 'a2dissite', f"{old_domain}.conf"], check=True)
#         subprocess.run(['sudo', 'a2ensite', f"{new_domain}.conf"], check=True)

#         # Reload Apache to apply the changes
#         subprocess.run(['sudo', 'systemctl', 'reload', 'apache2'], check=True)

#         # Rename the document root directory
#         old_document_root = f"/home/*/{old_domain}"
#         new_document_root = f"/home/*/{new_domain}"

#         for old_dir in glob.glob(old_document_root):
#             if os.path.isdir(old_dir):
#                 new_dir = old_dir.replace(old_domain, new_domain)
#                 shutil.move(old_dir, new_dir)
#                 username = os.path.basename(new_dir)
#                 subprocess.run(['sudo', 'chown', '-R', f"{username}:{username}", new_dir], check=True)
#             else:
#                 logger.warning(f"Document root for {old_domain} does not exist.")

#         # Remove the old configuration file
#         os.remove(old_conf)

#         return f"Domain {old_domain} has been renamed to {new_domain}."
#     except Exception as e:
#         logger.error(f"Error updating domain: {str(e)}")
#         return f"Error updating domain: {str(e)}"


# def update_apache_config(old_username, new_username, domain_name):
#     try:
#         logger.debug(f"Old username: {old_username}")
#         logger.debug(f"New username: {new_username}")
#         logger.debug(f"Domain name: {domain_name}")

#         config_dir = '/etc/apache2/sites-available'
#         conf_path = os.path.join(config_dir, f"{domain_name}.conf")

#         # Use sudo for writing to conf_path
#         sudo_command = ['sudo', 'tee', conf_path]
#         with subprocess.Popen(sudo_command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE) as proc:
#             content = f"""
# <VirtualHost *:80>
#     ServerAdmin webmaster@{domain_name}
#     ServerName {domain_name}
#     DocumentRoot /home/{new_username}/{domain_name}/public_html/
#     <Directory /home/{new_username}/{domain_name}/public_html/>
#         AllowOverride all
#         Require all granted
#         Options FollowSymlinks
#         DirectoryIndex home.html 
#         Allow from all
#     </Directory>
#     ErrorLog /home/{new_username}/{domain_name}/logs/error.log
#     CustomLog /home/{new_username}/{domain_name}/logs/access.log combined
# </VirtualHost>
#             """
#             stdout, stderr = proc.communicate(input=content.encode())

#             if proc.returncode != 0:
#                 logger.error(f"Failed to write Apache config: {stderr.decode()}")
#                 return f"Error: {stderr.decode()}"

#         subprocess.run(['sudo', 'a2ensite', f"{domain_name}.conf"], check=True)
#         subprocess.run(['sudo', 'systemctl', 'reload', 'apache2'], check=True)

#         return f"Apache configuration updated for {old_username} -> {new_username}."
#     except subprocess.CalledProcessError as e:
#         logger.error(f"Error updating Apache config: {e}")
#         return f"Error updating Apache config: {str(e)}"
#     except Exception as e:
#         logger.error(f"Error: {str(e)}")
#         return f"Error: {str(e)}"

# def update_apache_config(old_username, new_username, domain_name):
#     try:
#         print(f"Old username: {old_username}")
#         print(f"New username: {new_username}")
        

#         config_dir = '/etc/apache2/sites-available'
#         conf_path = os.path.join(config_dir, f"{domain_name}.conf")
#         with open(conf_path, 'r') as file:
#             content = file.read()
        
#         if f"/home/{old_username}" in content:
#             old_document_root = f"/home/{old_username}/{domain_name}/public_html/"
#             new_document_root = f"/home/{new_username}/{domain_name}/public_html/"
#             content = content.replace(old_document_root, new_document_root)
            
#             old_directory = f"<Directory /home/{old_username}/{domain_name}/public_html/>"
#             new_directory = f"<Directory /home/{new_username}/{domain_name}/public_html/>"
#             content = content.replace(old_directory, new_directory)
            
#             with open(conf_path, 'w') as file:
#                 file.write(content)
            
#             subprocess.run(['sudo', 'a2ensite', f"{domain_name}.conf"], check=True)
#             subprocess.run(['sudo', 'systemctl', 'reload', 'apache2'], check=True)

#             print("new_directory ")
            
#             return f"Apache configuration updated for {old_username} -> {new_username}."
            
#     except subprocess.CalledProcessError as e:
#         return f"Error updating Apache config: {str(e)}"
#     except Exception as e:
#         return f"Error: {str(e)}"





# def read_credentials_from_file():
#     credentials_file = '/var/www/html/popopanel/djangoproject/panel_credentials.txt'
#     credentials = {}
#     try:
#         with open(credentials_file, 'r') as file:
#             for line in file:
#                 key, value = line.strip().split(': ')
#                 credentials[key] = value
#     except FileNotFoundError:
#         print(f"File {credentials_file} not found.")
#     except Exception as e:
#         print(f"An error occurred: {e}")
#     return credentials



def read_credentials_from_file():
    credentials_file = '/var/www/html/popopanel/djangoproject/panel_credentials.txt'
    credentials = {}
    try:
        with open(credentials_file, 'r') as file:
            for line in file:
                key, value = line.strip().split(': ')
                credentials[key] = value
    except FileNotFoundError:
        print(f"File {credentials_file} not found.")
    except Exception as e:
        print(f"An error occurred: {e}")
    return credentials



def LoginPage(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        # Read credentials from the file
        credentials = read_credentials_from_file()
        stored_username = credentials.get('username')
        stored_password = credentials.get('password')

        # Validate the credentials
        if username == stored_username and password == stored_password:
            # Login successful
            request.session['username'] = username
            messages.success(request, 'Login successful!')
            return redirect('home')  # Redirect to home or dashboard page upon successful login
        else:
            # Invalid credentials
            messages.error(request, 'Invalid username or password.')
            return render(request, 'user/index.html')  # Make sure the template path is correct

    else:
        # Handle GET request or initial rendering of the login form
        return render(request, 'user/index.html')  # Make sure the template path is correct