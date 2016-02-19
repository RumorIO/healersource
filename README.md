# Healersource

## Test with py.test
Used options in pytest.ini --nomigrations, --reuse-db.

### Install
```bash
sudo pip install git+git://github.com/pytest-dev/pytest-django.git
sudo pip install pytest-pythonpath
```

### Usage
[Documentation](http://pytest.org/latest/usage.html#usage)

```bash
# with db recreate
py.test --create-db

# to ignore directory
py.test --ignore=apps/payments

# to run only test_appointments_view_correct_response from apps/clients directory
py.test apps/clients -k test_appointments_view_correct_response  
```

### With coverage report
```bash
sudo pip install pytest-cov

py.test --cov=. --cov-report=html
```
