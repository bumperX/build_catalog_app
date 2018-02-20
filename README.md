# Item Catalog Web Application
This is a project for the Udacity [FSND Course](https://www.udacity.com/course/full-stack-web-developer-nanodegree--nd004).

## Description
This app is a RESTful web application using the Python framework Flask which accesses SQL database along with implementing third-party OAuth authentication.

## Dependencies
* [Vagrant](https://www.vagrantup.com)
* [Udacity Vagrantfile](https://github.com/udacity/fullstack-nanodegree-vm)
* [VirtualBox](https://www.virtualbox.org/wiki/Download_Old_Builds_5_1)

## Installation and Run
1. Install Vagrant & VirtualBox
2. Clone the Udacity Vagrantfile
3. Go to Vagrant directory and either clone this repo or download and place zip here
3. Launch the Vagrant VM (`vagrant up`)
4. Log into Vagrant VM (`vagrant ssh`)
5. Navigate to `cd/vagrant` as instructed in terminal
6. The app imports requests which is not on this vm. Run sudo pip install requests
7. (Optional)Insert fake data `python /item-catalog/populate_db.py`
8. Run application using `python /catalog/application.py`
9. Access the application locally using `http://localhost:5000`

## JSON Endpoints
Access JSON APIs from:

Catalog JSON: `/catalog/JSON`
    - Displays information for all categories

Category JSON: `/catalog/<category_name>/JSON`
    - Displays information for a specific category

Category Items JSON: `/catalog/<category_name>/<item_title>/JSON`
    - Displays information for a specific item


