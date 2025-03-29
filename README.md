# Kana Logistics Backend

Welcome to the Kana Logistics Backend repository. This project utilizes Django and Django REST Framework to provide a robust and scalable backend solution for Kana Logistics' operations.

## Features

- **API Development**: Leveraging Django REST Framework to build RESTful APIs for seamless integration with various clients.
- **Authentication**: Implementing secure authentication mechanisms to protect sensitive data and operations.
- **Data Management**: Utilizing Django's ORM for efficient database interactions and data integrity.
- **Documentation**: Providing comprehensive API documentation to facilitate easy integration and usage.

## Requirements

- **Python**: Version 3.9 or higher.
- **Django**: Versions 4.2, 5.0, 5.1, or 5.2.
- **Django REST Framework**: For building and managing APIs.

*Note: We highly recommend and officially support only the latest patch release of each Python and Django series.*

## Installation

1. **Clone the Repository**:

   ```bash
   git clone git@github.com:sarsolutionz/Kana-Logistics-Backend.git
   cd Kana-Logistics-Backend
   ```

2. **Set Up a Virtual Environment**:

   It's recommended to use a virtual environment to manage dependencies.

   ```bash
   python3 -m venv env
   source env/bin/activate  # On Windows, use 'env\Scripts\activate'
   ```

3. **Install Dependencies**:

   Install the required packages using pip.

   ```bash
   pip install -r requirements.txt
   ```

4. **Apply Migrations**:

   Set up the database by applying migrations.

   ```bash
   python manage.py migrate
   ```

5. **Create a Superuser**:

   Create an admin user to access the Django admin panel.

   ```bash
   python manage.py createsuperuser
   ```

   Follow the prompts to set the username, email, and password.

6. **Run the Development Server**:

   Start the server to begin development.

   ```bash
   python manage.py runserver
   ```

   The API will be accessible at `http://127.0.0.1:8000/`.

## API Documentation

For detailed API documentation, including available endpoints, request/response formats, and authentication details, please refer to the [Django REST Framework Documentation](https://www.django-rest-framework.org/).

## Contributing

We welcome contributions to improve the Kana Logistics Backend. To contribute:

1. Fork the repository.
2. Create a new branch for your feature or bug fix.
3. Implement your changes.
4. Ensure that your code passes existing tests and includes new tests if applicable.
5. Submit a pull request detailing your changes.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

*For more information on Django REST Framework, visit the [official website](https://www.django-rest-framework.org/).*
