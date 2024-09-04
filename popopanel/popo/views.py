from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from django.http import HttpResponse
import logging
import subprocess
from django.contrib import messages
import os
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_protect
from popo.models import Customer , Website
import time
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth import authenticate, login, logout
from django.contrib.sessions.models import Session
from django.utils import timezone
from popo.models import User
from popo.models import Website
logger = logging.getLogger(__name__)
from django.shortcuts import render, get_object_or_404
import os
import pwd
import grp
import stat
from django.utils.timezone import datetime

import subprocess
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Customer, Website




def additional_ftp(request, website_id):
    website = get_object_or_404(Website, id=website_id)

    # Define the base directory for the website's FTP user, including the domain name
    base_dir = os.path.join('/home', website.ftp_username, website.website_name)
    
    # Initialize the directories list
    directories = []

    def list_directories(path, parent=None):
        # Get directories in the current path
        directories_list = []
        for entry in os.scandir(path):
            if entry.is_dir():
                dir_info = {'name': entry.name, 'subdirectories': []}
                # Recursively find subdirectories
                subdirs = list_directories(entry.path, parent=dir_info)
                if subdirs:
                    dir_info['subdirectories'] = subdirs
                directories_list.append(dir_info)
        return directories_list

    directories = list_directories(base_dir)

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        specific_directory = request.POST.get('specific_directory')

        if username and password and specific_directory:
            try:
                specific_path = os.path.join(base_dir, specific_directory)
                
                # Ensure the directory exists
                if not os.path.isdir(specific_path):
                    os.makedirs(specific_path)
                    
                # subprocess.run(['sudo', 'chmod', '755', base_dir], check=True)
                # Set permissions to 755 for the selected directory
                
                
                
                # Configure vsftpd to restrict the user to the selected directory
                vsftpd_conf = f"""
                local_root={os.path.join(base_dir, specific_directory)}
                write_enable=YES
                local_umask=022
                file_open_mode=0755
                chroot_local_user=YES
                allow_writeable_chroot=YES
                """

                # Write the vsftpd configuration for the new user
                conf_path = f'/etc/vsftpd/user_conf/{username}'
                with open(conf_path, 'w') as conf_file:
                    conf_file.write(vsftpd_conf)

                # Change the ownership of the configuration file to the vsftpd user
                subprocess.run(['sudo', 'chown', 'root:root', conf_path], check=True)
                subprocess.run(['sudo', 'chmod', '644', conf_path], check=True)

                # Add the user to the system with no shell access
                subprocess.run(['sudo', 'useradd', '-m', '-d', f'/home/{username}', '-s', '/bin/bash', username], check=True)
                subprocess.run(['sudo', 'chpasswd'], input=f'{username}:{password}', text=True, check=True)

                # Change the ownership of the user's home directory to the new user
                user_home_dir = f'/home/{username}'
                subprocess.run(['sudo', 'chown', '-R', f'{username}:{username}', user_home_dir], check=True)

                subprocess.run(['sudo', 'chmod', '775', specific_path], check=True)
                subprocess.run(['sudo', 'chown', '-R', f'{username}:{website.ftp_username}', specific_path], check=True)

                messages.success(request, 'FTP user created successfully!')
                return redirect('ftp_users', website.id)

            except Exception as e:
                messages.error(request, f'Error creating FTP user: {e}')
        else:
            messages.error(request, 'All fields are required.')

    context = {
        'website': website,
        'directories': directories,
    }
    return render(request, 'user/additional_ftp.html', context)




# Example function call
# additional_ftp(ftp_username='exampleuser', ftp_password='examplepass', specific_directory='/var/www/example', website_id=77)


def file_manager(request, website_id):
    website = get_object_or_404(Website, id=website_id)
    
    # Get the current directory from query parameters, default to root
    current_dir = request.GET.get('dir', '')
    
    # Construct the full path based on the current directory
    base_directory = f"/home/{website.ftp_username}/{website.website_name}"
    file_directory = os.path.join(base_directory, current_dir)

    # Ensure the user isn't attempting to access directories outside their allowed path
    if not file_directory.startswith(base_directory):
        raise Http404("Access denied")

    # Debug statement to print the directory being accessed
    print(f"Attempting to list directory: {file_directory}")
    
    # Get the list of files and directories with details
    try:
        files_and_dirs = os.listdir(file_directory)
        print(f"Found files and directories: {files_and_dirs}")  # Debug statement to print the contents
    except Exception as e:
        print(f"Error accessing directory: {e}")  # Debug statement to print any error that occurs
        files_and_dirs = []

    # Gather details for each file and directory
    entries = []
    for entry in files_and_dirs:
        entry_path = os.path.join(file_directory, entry)
        stat_info = os.stat(entry_path)
        entry_info = {
            'name': entry,
            'permissions': stat.filemode(stat_info.st_mode),  # Convert to human-readable format
            'size': stat_info.st_size,
            'owner': pwd.getpwuid(stat_info.st_uid).pw_name,
            'group': grp.getgrgid(stat_info.st_gid).gr_name,
            'modified_time': datetime.fromtimestamp(stat_info.st_mtime),
            'is_dir': os.path.isdir(entry_path),
        }
        entries.append(entry_info)

    # Generate the parent directory link
    parent_dir = os.path.dirname(current_dir) if current_dir else None

    context = {
        'website': website,
        'entries': entries,
        'current_dir': current_dir,
        'parent_dir': parent_dir,
    }
    return render(request, 'user/file_manager.html', context)




# import os
# from django.shortcuts import render, get_object_or_404
# from django.http import Http404

# def file_manager(request, website_id):
#     website = get_object_or_404(Website, id=website_id)
    
#     # Get the current directory from query parameters, default to root
#     current_dir = request.GET.get('dir', '')
    
#     # Construct the full path based on the current directory
#     base_directory = f"/home/{website.ftp_username}/{website.website_name}"
#     file_directory = os.path.join(base_directory, current_dir)

#     # Ensure the user isn't attempting to access directories outside their allowed path
#     if not file_directory.startswith(base_directory):
#         raise Http404("Access denied")

#     # Debug statement to print the directory being accessed
#     print(f"Attempting to list directory: {file_directory}")
    
#     # Get the list of files and directories
#     try:
#         files_and_dirs = os.listdir(file_directory)
#         print(f"Found files and directories: {files_and_dirs}")  # Debug statement to print the contents
#     except Exception as e:
#         print(f"Error accessing directory: {e}")  # Debug statement to print any error that occurs
#         files_and_dirs = []

#     # Separate files and directories for better display
#     files = [f for f in files_and_dirs if os.path.isfile(os.path.join(file_directory, f))]
#     directories = [d for d in files_and_dirs if os.path.isdir(os.path.join(file_directory, d))]

#     # Generate the parent directory link
#     parent_dir = os.path.dirname(current_dir) if current_dir else None

#     context = {
#         'website': website,
#         'files': files,
#         'directories': directories,
#         'current_dir': current_dir,
#         'parent_dir': parent_dir,
#     }
#     return render(request, 'user/file_manager.html', context)


# import os
# from django.shortcuts import render, get_object_or_404

# def file_manager(request, website_id):
#     website = get_object_or_404(Website, id=website_id)
    
#     # Define the directory path based on the website's FTP username
#     file_directory = f"/home/{website.ftp_username}/{website.website_name}"
#     print(f"Directory Path: {file_directory}")
    
#     # Get the list of files and directories
#     try:
#         files_and_dirs = os.listdir(file_directory)
#         print(f"Found files and directories: {files_and_dirs}")  # Debug statement to print the contents
#     except Exception as e:
#         print(f"Error accessing directory: {e}")  # Debug statement to print any error that occurs
#         files_and_dirs = []

#     # Separate files and directories for better display
#     files = [f for f in files_and_dirs if os.path.isfile(os.path.join(file_directory, f))]
#     directories = [d for d in files_and_dirs if os.path.isdir(os.path.join(file_directory, d))]

#     context = {
#         'website': website,
#         'files': files,
#         'directories': directories,
#     }
#     return render(request, 'user/file_manager.html', context)


def website_info(request, id):
    website = get_object_or_404(Website, id=id)
    logger.info(f"Website: {website}")  # Check if this appears in your logs
    return render(request, 'user/website_info.html', {'website': website})
# def website_info(request, id):
#     website = get_object_or_404(Website, id=id)
#     logger.info(f"Website: {website}")  # Check if this appears in your logs
#     return render(request, 'user/website_info.html', {'website': website})

# views.py
from django.shortcuts import render, get_object_or_404
from popo.models import Customer, Website


def customer_detail(request, customer_id):
    customer = get_object_or_404(Customer, id=customer_id)
    websites = Website.objects.filter(customer=customer)
    return render(request, 'user/customer_detail.html', {
        'customer': customer,
        'websites': websites
    })


@login_required
def list_customers(request):
    customers = Customer.objects.all()
    # for customer in customers:
    #     print(f"Customer ID: {customer.id}, Full Name: {customer.full_name}")
    return render(request, 'user/list_customers.html', {'customers': customers})

    
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
    

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from popo.models import Customer

def HomePage(request):
    if request.user.is_authenticated:
        # Admin user is logged in
        user_id = request.user.id
        return render(request, 'user/home.html', {'user_id': user_id})

    return redirect('login')

from django.shortcuts import render, redirect
from popo.models import Customer

def userhome(request):
    customer_id = request.session.get('customer_id')
    if customer_id:
        try:
            # Fetch the customer using the ID from the session
            customer = Customer.objects.get(id=customer_id)
            return render(request, 'user/userhome.html', {'customer': customer})
        except Customer.DoesNotExist:
            # If the customer does not exist, clear the session and redirect to login
            request.session.flush()
            return redirect('login')
    else:
        # No customer ID in session, redirect to login
        return redirect('login')


@login_required
def list_websites(request):
    user_id = request.user.id
    websites = Website.objects.all()
    return render(request, 'user/list_websites.html', {'websites': websites,'user_id': user_id })


import subprocess
import os
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.urls import reverse


def update_ftp_user(request, website_id):
    if request.method == 'POST':
        # Retrieve the website instance
        website = get_object_or_404(Website, id=website_id)

        # Get the current, new, and confirm FTP details from the form
        current_ftp_password = request.POST.get('current_ftp_password')
        new_ftp_password = request.POST.get('new_ftp_password')
        confirm_ftp_password = request.POST.get('confirm_ftp_password')
        new_ftp_username = request.POST.get('ftp_username')
        old_ftp_username = website.ftp_username

        if website.ftp_password != current_ftp_password:
            messages.error(request, "Current FTP password is incorrect.")
            return redirect(reverse('ftp_users', args=[website_id]))

        if new_ftp_password != confirm_ftp_password:
            messages.error(request, "New FTP passwords do not match.")
            return redirect(reverse('ftp_users', args=[website_id]))

        vsftpd_user_conf_dir = "/etc/vsftpd/user_conf/"
        old_vsftpd_user_conf = f"{vsftpd_user_conf_dir}/{old_ftp_username}"
        new_vsftpd_user_conf = f"{vsftpd_user_conf_dir}/{new_ftp_username}"

        apache_conf = f"/etc/apache2/sites-available/{website.website_name}.conf"
        apache_config_content = f"""
<VirtualHost *:80>
    ServerAdmin webmaster@{website.website_name}
    ServerName {website.website_name}
    DocumentRoot /home/{new_ftp_username}/{website.website_name}/public_html/
    <Directory /home/{new_ftp_username}/{website.website_name}/public_html/>
        AllowOverride all
        Require all granted
        Options FollowSymlinks
        DirectoryIndex home.html
        Allow from all
    </Directory>
    ErrorLog /home/{new_ftp_username}/{website.website_name}/logs/error.log
    CustomLog /home/{new_ftp_username}/{website.website_name}/logs/access.log combined
</VirtualHost>
        """

        try:
            # If the FTP username has changed, handle user and configuration updates
            if old_ftp_username != new_ftp_username:
                # Rename the user
                subprocess.run(['sudo', 'usermod', '-l', new_ftp_username, old_ftp_username], check=True)

                # Rename the home directory
                old_home_dir = f'/home/{old_ftp_username}'
                new_home_dir = f'/home/{new_ftp_username}'
                if os.path.exists(old_home_dir):
                    subprocess.run(['sudo', 'usermod', '-d', new_home_dir, '-m', new_ftp_username], check=True)
                else:
                    subprocess.run(['sudo', 'mkdir', '-p', new_home_dir], check=True)
                    subprocess.run(['sudo', 'usermod', '-d', new_home_dir, '-m', new_ftp_username], check=True)

                # Ensure the group exists or create it
                try:
                    subprocess.run(['sudo', 'groupadd', new_ftp_username], check=True)
                except subprocess.CalledProcessError:
                    # Ignore the error if the group already exists
                    pass

                # Set correct ownership and permissions
                subprocess.run(['sudo', 'chown', '-R', f'{new_ftp_username}:{new_ftp_username}', new_home_dir], check=True)
                subprocess.run(['sudo', 'chmod', '-R', '755', new_home_dir], check=True)

                # Delete the old vsftpd configuration
                if os.path.exists(old_vsftpd_user_conf):
                    subprocess.run(['sudo', 'rm', '-f', old_vsftpd_user_conf], check=True)
                    print(f"Deleted old vsftpd config: {old_vsftpd_user_conf}")

                # Update Apache virtual host configuration
                subprocess.run(f'sudo sh -c "echo \'{apache_config_content}\' > {apache_conf}"', shell=True, check=True)
                print(f"Apache virtual host configuration updated: {apache_conf}")

                # Update website's FTP username
                website.ftp_username = new_ftp_username

            # Update the password
            subprocess.run(['sudo', 'chpasswd'], input=f'{new_ftp_username}:{new_ftp_password}'.encode(), check=True)
            website.ftp_password = new_ftp_password

            # Ensure the vsftpd user configuration directory exists
            subprocess.run(['sudo', 'mkdir', '-p', vsftpd_user_conf_dir], check=True)

            # Create the new vsftpd configuration for the user
            vsftpd_config_content = f"""
local_root=/home/{new_ftp_username}
write_enable=YES
local_umask=022
file_open_mode=0755
            """
            subprocess.run(f'sudo sh -c "echo \'{vsftpd_config_content}\' > {new_vsftpd_user_conf}"', shell=True, check=True)

            # Restart vsftpd to apply changes
            subprocess.run(['sudo', 'systemctl', 'restart', 'vsftpd'], check=True)

            # Save the changes to the website instance
            website.save()

            # Provide a success message
            messages.success(request, f"FTP details for {website.website_name} updated successfully.")

        except subprocess.CalledProcessError as e:
            error_message = e.stderr.decode() if e.stderr else str(e)
            messages.error(request, f"Error updating FTP user: {error_message}")
            print(f"Debug Info: Command '{e.cmd}' returned non-zero exit status {e.returncode}.")

        # Redirect to the FTP details page
        return redirect(reverse('ftp_users', args=[website_id]))

    # If the request method is not POST, redirect to the website details page
    return redirect(reverse('website_info', args=[website_id]))



# import subprocess
# import os
# from django.shortcuts import get_object_or_404, redirect
# from django.contrib import messages
# from django.urls import reverse


# def update_ftp_user(request, website_id):
#     if request.method == 'POST':
#         # Retrieve the website instance
#         website = get_object_or_404(Website, id=website_id)

#         # Get the new FTP details from the form
#         new_ftp_username = request.POST.get('ftp_username')
#         new_ftp_password = request.POST.get('ftp_password')
#         old_ftp_username = website.ftp_username

#         try:
#             vsftpd_user_conf_dir = "/etc/vsftpd/user_conf/"
#             old_vsftpd_user_conf = f"{vsftpd_user_conf_dir}/{old_ftp_username}"
#             new_vsftpd_user_conf = f"{vsftpd_user_conf_dir}/{new_ftp_username}"

#             # If the FTP username has changed, rename the existing user and remove the old vsftpd config
#             if old_ftp_username != new_ftp_username:
#                 # Rename the user
#                 subprocess.run(['sudo', 'usermod', '-l', new_ftp_username, old_ftp_username], check=True)

#                 # Rename the home directory
#                 old_home_dir = f'/home/{old_ftp_username}'
#                 new_home_dir = f'/home/{new_ftp_username}'
#                 if os.path.exists(old_home_dir):
#                     subprocess.run(['sudo', 'usermod', '-d', new_home_dir, '-m', new_ftp_username], check=True)
#                 else:
#                     subprocess.run(['sudo', 'mkdir', '-p', new_home_dir], check=True)
#                     subprocess.run(['sudo', 'usermod', '-d', new_home_dir, '-m', new_ftp_username], check=True)

#                 # Ensure the group exists or create it
#                 try:
#                     subprocess.run(['sudo', 'groupadd', new_ftp_username], check=True)
#                 except subprocess.CalledProcessError:
#                     # Ignore the error if the group already exists
#                     pass

#                 # Set correct ownership and permissions
#                 subprocess.run(['sudo', 'chown', '-R', f'{new_ftp_username}:{new_ftp_username}', new_home_dir], check=True)
#                 subprocess.run(['sudo', 'chmod', '-R', '755', new_home_dir], check=True)

#                 # Delete the old vsftpd configuration
#                 if os.path.exists(old_vsftpd_user_conf):
#                     subprocess.run(['sudo', 'rm', '-f', old_vsftpd_user_conf], check=True)
#                     print(f"Deleted old vsftpd config: {old_vsftpd_user_conf}")

#                 website.ftp_username = new_ftp_username

#             # Update the password
#             subprocess.run(['sudo', 'chpasswd'], input=f'{new_ftp_username}:{new_ftp_password}'.encode(), check=True)
#             website.ftp_password = new_ftp_password

#             # Ensure the vsftpd user configuration directory exists
#             subprocess.run(['sudo', 'mkdir', '-p', vsftpd_user_conf_dir], check=True)

#             # Create the new vsftpd configuration for the user
#             vsftpd_config_content = f"""
# local_root=/home/{new_ftp_username}
# write_enable=YES
# local_umask=022
# file_open_mode=0755
#             """
#             subprocess.run(f'sudo sh -c "echo \'{vsftpd_config_content}\' > {new_vsftpd_user_conf}"', shell=True, check=True)

#             # Restart vsftpd to apply changes
#             subprocess.run(['sudo', 'systemctl', 'restart', 'vsftpd'], check=True)

#             # Save the changes to the website instance
#             website.save()

#             # Provide a success message
#             messages.success(request, f"FTP details for {website.website_name} updated successfully.")

#         except subprocess.CalledProcessError as e:
#             error_message = e.stderr.decode() if e.stderr else str(e)
#             messages.error(request, f"Error updating FTP user: {error_message}")
#             print(f"Debug Info: Command '{e.cmd}' returned non-zero exit status {e.returncode}.")

#         # Redirect to the FTP details page
#         return redirect(reverse('ftp_users', args=[website_id]))

#     # If the request method is not POST, redirect to the website details page
#     return redirect(reverse('website_info', args=[website_id]))



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

    return render(request, 'user/add_customer.html', {'user_id': user_id })


import subprocess
import os

def create_ftp_user(ftp_username, ftp_password):
    try:
        # Check if the user already exists
        user_exists = subprocess.run(['id', '-u', ftp_username], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        if user_exists.returncode != 0:
            raise Exception(f"FTP user {ftp_username} does not exist. Please create the user first.")

        # Set or update the password for the FTP user
        subprocess.run(['sudo', 'chpasswd'], input=f'{ftp_username}:{ftp_password}'.encode(), check=True)

        # Ensure the vsftpd user configuration directory exists
        vsftpd_user_conf_dir = "/etc/vsftpd/user_conf/"
        subprocess.run(['sudo', 'mkdir', '-p', vsftpd_user_conf_dir], check=True)

        # Create vsftpd configuration for the user
        vsftpd_user_conf = os.path.join(vsftpd_user_conf_dir, ftp_username)
        vsftpd_config_content = f"""
local_root= /home/{ftp_username}
write_enable=YES
local_umask=022
file_open_mode=0755
        """

        with open(vsftpd_user_conf, 'w') as conf_file:
            conf_file.write(vsftpd_config_content)

        # Change the ownership of the configuration file to root:root
        subprocess.run(['sudo', 'chown', 'root:root', vsftpd_user_conf], check=True)

        print(f"FTP configuration for {ftp_username} completed successfully.")
        
    except subprocess.CalledProcessError as e:
        error_message = e.stderr.decode() if e.stderr else str(e)
        raise Exception(f'Error creating FTP user: {error_message}')
    except IOError as e:
        raise Exception(f'Error writing vsftpd configuration file: {str(e)}')

from django.shortcuts import render, redirect, get_object_or_404
from .models import Website
from django.contrib import messages

import os
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages

import os
import logging
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from .models import Website

import os
import subprocess
import logging
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages

logger = logging.getLogger(__name__)

def update_php_version(request, website_id):
    website = get_object_or_404(Website, id=website_id)
    current_php_version = website.php_version

    if request.method == 'POST':
        new_php_version = request.POST.get('new_php_version')
        if new_php_version:
            try:
                # Call your function to install and configure PHP
                install_php_and_configure(website.ftp_username, website.website_name, new_php_version)
                
                # Define the Apache configuration file path and content
                apache_conf = f"/etc/apache2/sites-available/{website.website_name}.conf"
                temp_apache_conf = f"/tmp/{website.website_name}.conf"
                apache_config_content = f"""
<VirtualHost *:80>
    ServerAdmin webmaster@{website.website_name}
    ServerName {website.website_name}
    DocumentRoot /home/{website.ftp_username}/{website.website_name}/public_html/
    <Directory /home/{website.ftp_username}/{website.website_name}/public_html/>
        AllowOverride all
        Require all granted
        Options FollowSymlinks
        DirectoryIndex home.html 
        Allow from all
    </Directory>
    ErrorLog /home/{website.ftp_username}/{website.website_name}/logs/error.log
    CustomLog /home/{website.ftp_username}/{website.website_name}/logs/access.log combined
    # Configure PHP-FPM
    <FilesMatch \.php$>
        SetHandler "proxy:unix:/run/php/php{new_php_version}-fpm-{website.ftp_username}.sock|fcgi://localhost"
    </FilesMatch>
</VirtualHost>
                """
                
                # Write to the temporary file
                with open(temp_apache_conf, 'w') as f:
                    f.write(apache_config_content)

                # Change permissions of the temporary file
                os.chmod(temp_apache_conf, 0o644)

                # Move the temporary file to the Apache configuration directory
                result = subprocess.run(['sudo', 'mv', temp_apache_conf, apache_conf], capture_output=True, text=True)
                if result.returncode != 0:
                    raise Exception(f"Failed to move configuration file: {result.stderr}")

                php_fpm_service = f'php{new_php_version}-fpm'
                result = subprocess.run(['sudo', 'systemctl', 'restart', php_fpm_service], capture_output=True, text=True)
                if result.returncode != 0:
                    raise Exception(f"Failed to restart PHP-FPM service: {result.stderr}")

                # Reload Apache to apply the changes
                # result = subprocess.run(['sudo', 'systemctl', 'reload', 'apache2'], capture_output=True, text=True)
                # if result.returncode != 0:
                #     raise Exception(f"Failed to reload Apache: {result.stderr}")

                # Update the PHP version in the database
                website.php_version = new_php_version
                website.save()

                messages.success(request, 'PHP version updated successfully and Apache configuration updated.')
            except Exception as e:
                logger.error(f"Failed to update Apache configuration: {e}")
                messages.error(request, f"Failed to update Apache configuration: {e}")

            return redirect('update_php_version', website_id=website_id)

    return render(request, 'user/update_php_version.html', {'website': website, 'current_php_version': current_php_version})



def install_php_and_configure(ftp_username, website_name, php_version):
    """
    Install PHP and configure PHP-FPM for the given user and domain.

    Args:
        ftp_username (str): The FTP username for which PHP should be configured.
        website_name (str): The domain name for the website.
        php_version (str): The PHP version to install and configure.
    """
    try:
        
        
        # subprocess.run(['sudo', 'ls'], check=True, capture_output=True, text=True)
        # print("Sudo access verified successfully.")
        # Update package list and install PHP if not already installed
        if subprocess.call(['lsb_release', '-a'], stdout=subprocess.PIPE, stderr=subprocess.PIPE) == 0:  # Check for Debian-based
            subprocess.run(['sudo', 'apt', 'update'], check=True)
            subprocess.run(['sudo', 'apt', 'install', '-y', f'php{php_version}', f'php{php_version}-fpm'], check=True)
        else:  # Assume RedHat-based
            subprocess.run(['sudo', 'yum', 'install', '-y', f'php{php_version}', f'php{php_version}-fpm'], check=True)



        # Create PHP-FPM configuration file
        fpm_conf = f'/etc/php/{php_version}/fpm/pool.d/{ftp_username}.conf'
        fpm_config_content = f"""
[{ftp_username}]
user = {ftp_username}
group = {ftp_username}
listen = /run/php/php{php_version}-fpm-{ftp_username}.sock
listen.owner = www-data
listen.group = www-data
listen.mode = 0660
pm = dynamic
pm.max_children = 5
pm.start_servers = 2
pm.min_spare_servers = 1
pm.max_spare_servers = 3
chdir = /
        """
        # Use a temporary file to store the configuration content and then move it
        temp_conf_file = f'/tmp/{ftp_username}.conf'
        with open(temp_conf_file, 'w') as f:
            f.write(fpm_config_content)

        # Move the temporary file to the target location
        subprocess.run(['sudo', 'mv', temp_conf_file, fpm_conf], check=True)
        subprocess.run(['sudo', 'chown', 'root:root', fpm_conf], check=True)
        subprocess.run(['sudo', 'chmod', '644', fpm_conf], check=True)

        # Ensure PHP-FPM service is active
        php_fpm_service = f'php{php_version}-fpm'
        subprocess.run(['sudo', 'systemctl', 'start', php_fpm_service], check=True)
        subprocess.run(['sudo', 'systemctl', 'enable', php_fpm_service], check=True)
        
        subprocess.run(['sudo', 'systemctl', 'reload', 'apache2'], check=True)

        print(f"PHP {php_version} installed and configured for user {ftp_username}.")
    except subprocess.CalledProcessError as e:
        print(f"Error during PHP installation: {e}")



from django.shortcuts import render, redirect
from django.contrib import messages

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Website  # Import your Website model
import subprocess
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Website

def add_database(request, website_id):
    # Fetch the website object based on the provided website_id
    selected_website = get_object_or_404(Website, id=website_id)

    if request.method == "POST":
        # Retrieve the input values from the POST request
        database_name = request.POST.get('database_name')
        database_user = request.POST.get('database_user')
        database_password = request.POST.get('database_password')

        if database_name and database_user and database_password:
            try:
                # Retrieve root database credentials from database_details table
                with connection.cursor() as cursor:
                    cursor.execute("SELECT username, password FROM database_detials WHERE id = 1;")
                    result = cursor.fetchone()
                    if result:
                        username, password = result
                    else:
                        raise RuntimeError("Database credentials not found in the database_details table.")

                # MySQL command prefix with root credentials
                mysql_command = ['mysql', '-u', username, f'-p{password}']

                # Create the database
                subprocess.run(
                    mysql_command + ['-e', f"CREATE DATABASE {database_name};"],
                    check=True, capture_output=True, text=True
                )

                # Create the database user
                subprocess.run(
                    mysql_command + ['-e', f"CREATE USER '{database_user}'@'localhost' IDENTIFIED BY '{database_password}';"],
                    check=True, capture_output=True, text=True
                )

                # Grant all privileges to the new user on the new database
                subprocess.run(
                    mysql_command + ['-e', f"GRANT ALL PRIVILEGES ON {database_name}.* TO '{database_user}'@'localhost';"],
                    check=True, capture_output=True, text=True
                )

                # Flush privileges to ensure all changes take effect
                subprocess.run(
                    mysql_command + ['-e', "FLUSH PRIVILEGES;"],
                    check=True, capture_output=True, text=True
                )

                # Display a success message
                messages.success(request, f"Database {database_name} created successfully!")
                # Redirect to the website details page
                return redirect('website_details', website_id=selected_website.id)
            except subprocess.CalledProcessError as e:
                # Handle errors in the subprocess execution
                error_message = e.stderr if e.stderr else str(e)
                messages.error(request, f"An error occurred while creating the database and user: {error_message}")
        else:
            # Display an error message if required fields are missing
            messages.error(request, "All fields are required.")

    # Render the add database template
    return render(request, 'user/add_database.html', {'website': selected_website})

import random
import string
from django.db import connection

def create_database_and_user(ftp_username, website_name, length=8):
    # Retrieve root database credentials from database_details table
    with connection.cursor() as cursor:
        cursor.execute("SELECT username, password FROM database_detials WHERE id = 1;")
        result = cursor.fetchone()
        if result:
            username, password = result
            print(f"Root Username: {username}")
            print(f"Root Password: {password}")
        else:
            raise RuntimeError("Database credentials not found in the database_detials table.")

    # Generate random database, user, and password
    db_name = f"db_{''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(6))}"
    db_user = f"user_{''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(6))}"
    db_pass = ''.join(random.choice(string.ascii_letters ) for _ in range(length))

    try:
        # Print generated values
        print(f"Database Name: {db_name}")
        print(f"Database User: {db_user}")
        print(f"Database Password: {db_pass}")

        # MySQL command prefix with root credentials
        mysql_command = ['mysql', '-u', username, f'-p{password}']

        # Create database
        result = subprocess.run(
            mysql_command + ['-e', f"CREATE DATABASE {db_name};"],
            check=True, capture_output=True, text=True
        )
        print("Create Database Output:", result.stdout)

        # Create user
        result = subprocess.run(
            mysql_command + ['-e', f"CREATE USER '{db_user}'@'localhost' IDENTIFIED BY '{db_pass}';"],
            check=True, capture_output=True, text=True
        )
        print("Create User Output:", result.stdout)

        # Grant privileges
        result = subprocess.run(
            mysql_command + ['-e', f"GRANT ALL PRIVILEGES ON {db_name}.* TO '{db_user}'@'localhost';"],
            check=True, capture_output=True, text=True
        )
        print("Grant Privileges Output:", result.stdout)

        # Flush privileges
        result = subprocess.run(
            mysql_command + ['-e', "FLUSH PRIVILEGES;"],
            check=True, capture_output=True, text=True
        )
        print("Flush Privileges Output:", result.stdout)

        return {
            'db_name': db_name,
            'db_user': db_user,
            'db_pass': db_pass,
        }

    except subprocess.CalledProcessError as e:
        error_message = e.stderr if e.stderr else str(e)
        raise RuntimeError(f"An error occurred while creating the database and user: {error_message}")





@login_required
def add_website(request):
    customers = Customer.objects.all()
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
            
            # Call the PHP installation and configuration function
            

            # Create user and other setup tasks
            create_user_command = ['sudo', 'useradd', ftp_username]
            subprocess.run(create_user_command, check=True)

            create_dirs_command = ['sudo', 'mkdir', '-p', f'/home/{ftp_username}/{website_name}/public_html', f'/home/{ftp_username}/{website_name}/logs']
            subprocess.run(create_dirs_command, check=True)

            set_permissions_command = ['sudo', 'chown', '-R', f'{ftp_username}:{ftp_username}', f'/home/{ftp_username}', f'/home/{ftp_username}/{website_name}']
            subprocess.run(set_permissions_command, check=True)
            subprocess.run(['sudo', 'chmod', '-R', '755', f'/home/{ftp_username}/{website_name}'], check=True)

            subprocess.run(['sudo', '-u', ftp_username, 'touch', f'/home/{ftp_username}/{website_name}/logs/error.log', f'/home/{ftp_username}/{website_name}/logs/access.log'], check=True)
            
            create_ftp_user(ftp_username, ftp_password)

            install_php_and_configure(ftp_username, website_name, php_version)

            create_database_and_user(ftp_username, website_name)


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
    # Configure PHP-FPM
    <FilesMatch \.php$>
        SetHandler "proxy:unix:/run/php/php{php_version}-fpm-{ftp_username}.sock|fcgi://localhost"
    </FilesMatch>
</VirtualHost>
            """
            with open(apache_conf, 'w') as f:
                f.write(apache_config_content)

            subprocess.run(['sudo', 'chown', 'root:root', apache_conf], check=True)

            # Enable Apache site configuration
            subprocess.run(['sudo', 'a2ensite', f'{website_name}.conf'], check=True)
           

             # Reload and restart PHP-FPM service with root privileges
            subprocess.run(['sudo', 'systemctl', 'reload', f'php{php_version}-fpm'], check=True)
            subprocess.run(['sudo', 'systemctl', 'restart', f'php{php_version}-fpm'], check=True)

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

    php_versions = ['7.4', '8.0', '8.1']  # Example PHP versions
    return render(request, 'user/add_website.html', {'customers': customers, 'php_versions': php_versions, 'user_id': user_id})

# @csrf_protect
# @login_required
# def add_website(request):
#     customers = Customer.objects.all()
#     user_id = request.user.id
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

#             create_ftp_user(ftp_username, ftp_password)

#             # Create necessary directories with sudo
#             create_dirs_command = ['sudo',  '-u', 'root','mkdir', '-p', f'/home/{ftp_username}/{website_name}/public_html', f'/home/{ftp_username}/{website_name}/logs']
#             subprocess.run(create_dirs_command, check=True)

#             # Set permissions for directories and files
#             set_permissions_command = ['sudo', 'chown', '-R', f'{ftp_username}:{ftp_username}', f'/home/{ftp_username}', f'/home/{ftp_username}/{website_name}']
#             subprocess.run(set_permissions_command, check=True)
#             subprocess.run(['sudo', 'chmod', '-R', '755', f'/home/{ftp_username}/{website_name}'], check=True)

#             # Create logs files
#             subprocess.run(['sudo', '-u', ftp_username, 'touch', f'/home/{ftp_username}/{website_name}/logs/error.log', f'/home/{ftp_username}/{website_name}/logs/access.log'], check=True)

#             # Create index.html file using touch command
#             # subprocess.run(['sudo', '-u', ftp_username, 'touch', f'/home/{ftp_username}/{website_name}/public_html/home.html'], check=True)

#             # Set permissions for index.html
#             # subprocess.run(['sudo', 'chmod', '755', f'/home/{ftp_username}/{website_name}/public_html/home.html'], check=True)

#             # Modify user's shell configuration file to change directory upon login
#             subprocess.run(f'sudo sh -c "echo \'cd /home/{ftp_username}/{website_name}\' >> \'/home/{ftp_username}/.bashrc\'"', shell=True, check=True)

#             # Set up DNS resolution locally
            # subprocess.run(f'sudo sh -c "echo \'192.168.3.239    {website_name}\' >> \'/etc/hosts\'"', shell=True, check=True)
            # print(f"DNS resolution set up for domain {website_name}.")

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
#     return render(request, 'user/add_website.html', {'customers': customers, 'php_versions': php_versions , 'user_id': user_id})



# from django.contrib.auth import authenticate, login
# from django.shortcuts import render, redirect
# from django.contrib import messages
# from popo.models import User, Customer
# from popo.auth_backends import CustomBackend, CustomerBackend

# def login_view(request):
#     if request.method == 'POST':
#         username = request.POST['username']
#         password = request.POST['password']

#         print(f"Username: {username}")
#         print(f"Entered Password: {password}")

#         # First, attempt to authenticate as an admin user
#         user = CustomBackend().authenticate(request, username=username, password=password)

#         if user is not None:
#             print("Admin password match found, logging in user.")
#             login(request, user, backend='popo.auth_backends.CustomBackend')  # Specify the backend
            
#             # Print user details to the terminal
#             print(f"Authenticated User: {user.username}")
#             print(f"User Email: {user.emailid}")
#             print(f"User is Active: {user.is_active}")
#             print(f"User is Admin: {user.is_admin}")

#             return redirect('home')  # Redirect to the home page after successful login
        
#         else:
#             # If admin login fails, check for customer login
#             customer = CustomerBackend().authenticate(request, username=username, password=password)
#             if customer is not None:
#                 print("Customer login successful.")
                
#                 # Manually log the customer in by setting the session
#                 request.session['customer_id'] = customer.id
#                 request.session['customer_email'] = customer.email
#                 request.session.modified = True
#                 print(f"Session Data: {request.session.items()}")
                
#                 # Try redirecting to a different page first
#                 return redirect('userhome')
#             else:
#                 print("Password mismatch or user does not exist.")
#                 messages.error(request, 'Invalid username or password')

#     return render(request, 'user/index.html')



# def logout_view(request):
#     # Get the current user's ID
#     user_id = request.user.id

#     # Print user_id for debugging
#     print(f"User ID: {user_id}")

#     # Invalidate all sessions for the user
#     sessions = Session.objects.filter(expire_date__gte=timezone.now())
#     print(sessions)
#     for session in sessions:
#         data = session.get_decoded()
#         print(data)
#         if data.get('_auth_user_id') == str(user_id):
#             session.delete()

#     # Log out the user
#     logout(request)
#     return redirect('index')



from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.sessions.models import Session
from django.utils import timezone
from popo.models import User, Customer
from popo.auth_backends import CustomBackend, CustomerBackend

from django.utils.cache import add_never_cache_headers

def login_view(request):
    # Check if the user is already authenticated
    if request.user.is_authenticated:
        print("User is already authenticated, redirecting to home page.")
        return redirect('home')  # Redirect to the home page if already logged in

    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        print(f"Username: {username}")
        print(f"Entered Password: {password}")

        # First, attempt to authenticate as an admin user
        user = CustomBackend().authenticate(request, username=username, password=password)

        if user is not None:
            print("Admin password match found, logging in user.")
            login(request, user, backend='popo.auth_backends.CustomBackend')  # Specify the backend

            # Print user details to the terminal
            print(f"Authenticated User: {user.username}")
            print(f"User Email: {user.emailid}")
            print(f"User is Active: {user.is_active}")
            print(f"User is Admin: {user.is_admin}")

            return redirect('home')  # Redirect to the home page after successful login
        
        else:
            # If admin login fails, check for customer login
            customer = CustomerBackend().authenticate(request, username=username, password=password)
            if customer is not None:
                print("Customer login successful.")

                # Manually log the customer in by setting the session
                request.session['customer_id'] = customer.id
                request.session['customer_email'] = customer.email
                request.session.modified = True
                print(f"Session Data: {request.session.items()}")

                # Redirect to the user home page
                return redirect('userhome')
            else:
                print("Password mismatch or user does not exist.")
                messages.error(request, 'Invalid username or password')

    # Prevent browser from caching the login page
    response = render(request, 'user/index.html')
    add_never_cache_headers(response)  # Prevent caching
    return response


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
