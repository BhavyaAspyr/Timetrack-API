# authapp/views.py

from rest_framework.views import APIView
from rest_framework.response import Response
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from rest_framework import status
from django.contrib.auth.hashers import make_password, check_password
import jwt
from django.conf import settings

# authapp/views.py

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import psycopg  # PostgreSQL driver (if not installed, use `pip install psycopg[binary]`)
from django.conf import settings


class SignupView(APIView):
    def post(self, request):
        # Extract data from the request body
        email = request.data.get('email')
        username = request.data.get('username')
        password = request.data.get('password')
        role = request.data.get('role')

        hash_password = make_password(password)

        # Validate input data
        if not email or not username or not password:
            return Response(
                {'error': 'Email, username, and password are required fields'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Connect to the PostgreSQL database
            connection = psycopg.connect(
                dbname='users', 
                user='postgres',  # Replace with your DB username
                password='Aspyr12345!',  # Replace with your DB password
                host='localhost',  # Adjust if different
                port='5432'  # Adjust if using a different port
            )
            cursor = connection.cursor()

            # Insert data into the credentials table
            insert_query = """
                INSERT INTO credentials (email, username, password, role)
                VALUES (%s, %s, %s, %s)
            """
            cursor.execute(insert_query, (email, username, hash_password, role))
            connection.commit()

            return Response({'message': 'User registered successfully'}, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        finally:
            # Close the connection
            if connection:
                cursor.close()
                connection.close()


class AuthenticateView(APIView):
    def post(self, request):
        # Extract usr_id and usr_pass from the request body
        usr_id = request.data.get('email')
        usr_pass = request.data.get('password')

        # Check if usr_id and usr_pass are provided
        if not usr_id or not usr_pass:
            return Response({'error': 'Both usr_id and usr_pass are required'}, status=400)


        try:
            # Connect to the PostgreSQL database
            connection = psycopg.connect(
                dbname='users', 
                user='postgres',  # Replace with your DB username
                password='Aspyr12345!',  # Replace with your DB password
                host='localhost',  # Adjust if different
                port='5432'  # Adjust if using a different port
            )
            cursor = connection.cursor()

            cursor.execute("""
            SELECT password, username
            FROM credentials
            WHERE email = %s
            """, (usr_id,))

            password, username = cursor.fetchone()
            print(cursor.fetchone())

            if check_password(usr_pass, password):
                print('Authenticated')
                # Generate JWT token if authentication is successful
                payload = {'login': usr_id, 'password': password}
                token = jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')
                #strore token to cookies
                #access token and refreshed tokens
                return Response({'message': 'Authenticated successfully', 'token': token, 'resource':username, "status": 200}, status=200)
            else:
                return Response({'error': 'Invalid usr_id or usr_pass'}, status=401)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        finally:
            # Close the connection
            if connection:
                cursor.close()
                connection.close()

        # Authenticate the user
        # user = authenticate(email=usr_id, password=usr_pass)

        # if user is not None:
        #     # Generate JWT token if authentication is successful
        #     payload = {'user_id': user.id, 'username': user.username}
        #     token = jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')
        #     return Response({'message': 'Authenticated successfully', 'token': token}, status=200)
        # else:
        #     return Response({'error': 'Invalid usr_id or usr_pass'}, status=401)
  