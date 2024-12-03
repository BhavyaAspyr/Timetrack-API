import psycopg
from psycopg import sql
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from .authenticate import authenticate_request
from datetime import datetime, timedelta
from contextlib import contextmanager
from psycopg import connect

def get_db_connection():
    """Establish and return a database connection."""
    return connect(
        dbname='users',
        user='postgres',
        password='Aspyr12345!',
        host='localhost',
        port='5432'
    )


@contextmanager
def db_cursor():
    """Context manager for database connection and cursor."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        yield cursor
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()
        conn.close()


@csrf_exempt
def insert_time_data(request):
    if request.method == 'POST':
        # Parse the incoming JSON data
        data = json.loads(request.body)

        # Extract the resource from the input data
        parent_id = data.get('parent_id', '')
        resource = data.get('resource', '')  # Get the resource name

        # Extract the projects array containing time entries
        projects = data.get('projects', [])

        # Ensure the projects data is valid (not empty)
        if not projects:
            return JsonResponse({'status': 'error', 'message': 'No project data provided.'})

        # Connect to PostgreSQL database
        try:
            with db_cursor() as cursor:
                for entry in projects:
                    customer = entry['customer']
                    project_name = entry['project_name']
                    date = entry['date']
                    hours = entry['hours']
                    role = entry['role']

                    # Insert or update using ON CONFLICT
                    cursor.execute(
                        sql.SQL("""
                            INSERT INTO op_time_timetrack (tmt_resource, tmt_date, tmt_hours, tmt_customers, tmt_project, tmt_resource_role, parent_id)
                            VALUES (%s, %s, %s, %s, %s, %s, %s)
                            ON CONFLICT (tmt_resource, tmt_date, tmt_customers, tmt_project, tmt_resource_role)
                            DO UPDATE SET 
                                tmt_hours = EXCLUDED.tmt_hours
                        """),
                        [resource, date, hours, customer, project_name, role, parent_id]
                    )

            # Return a success response
            return JsonResponse({'status': 'success', 'message': 'Data inserted or updated successfully.', 'parent_id': parent_id})

        except Exception as e:
            # Handle database connection errors or query errors
            return JsonResponse({'status': 'error', 'message': str(e)})

    return JsonResponse({'status': 'error', 'message': 'Invalid HTTP method. Only POST is allowed.'})


@csrf_exempt
def update_time_data(request):
    if request.method == 'PUT':
        try:
            # Parse the incoming JSON payload
            data = json.loads(request.body)

            # Extract `resource` from the top-level payload
            resource = data.get('resource', '').strip()  # Ensure it's non-empty and clean
            parent_id = data.get('parent_id', '').strip()
            projects = data.get('projects', [])

            # Validate `resource` and `parent_id`
            if not resource:
                return JsonResponse({'status': 'error', 'message': 'Resource is required.'}, status=400)
            if not parent_id:
                return JsonResponse({'status': 'error', 'message': 'Parent ID is required.'}, status=400)
            if not projects:
                return JsonResponse({'status': 'error', 'message': 'No projects provided.'}, status=400)

            # Connect to PostgreSQL
            with db_cursor() as cursor:

                # Update rows using `parent_id`, `tmt_date`, and `resource`
                for project in projects:
                    date = project.get('date')
                    hours = project.get('hours', 0)
                    customer = project.get('customer', '')
                    project_name = project.get('project_name', '')
                    role = project.get('role', '')

                    # Validate project fields
                    if not (date and customer and project_name and role):
                        return JsonResponse({'status': 'error', 'message': 'Incomplete project data.'}, status=400)

                    # Execute the SQL update query
                    cursor.execute(
                        """
                        UPDATE op_time_timetrack
                        SET 
                            tmt_hours = %s,
                            tmt_customers = %s,
                            tmt_project = %s,
                            tmt_resource_role = %s
                        WHERE 
                            parent_id = %s AND tmt_date = %s AND tmt_resource = %s
                        """,
                        [hours, customer, project_name, role, parent_id, date, resource]
                    )

            return JsonResponse({'status': 'success', 'message': 'Rows updated successfully.'})

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

    return JsonResponse({'status': 'error', 'message': 'Invalid HTTP method.'}, status=405)


@csrf_exempt
def track_hours(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON input.'})

        # Extract input parameters
        resource = data.get('resource', '').strip()
        start_date_str = data.get('start_date', '').strip()
        end_date_str = data.get('end_date', '').strip()

        if not resource or not start_date_str or not end_date_str:
            return JsonResponse({
                'status': 'error',
                'message': 'Resource, start date, and end date are required.'
            })

        try:
            # Parse the start and end dates
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
            week_dates = [(start_date + timedelta(days=i)).strftime('%Y-%m-%d') 
                          for i in range((end_date - start_date).days + 1)]

            with db_cursor() as cursor:

                # Query to fetch data, including parent_id
                query = """
                    SELECT parent_id, tmt_customers, tmt_project, tmt_date, 
                        COALESCE(tmt_hours, 0) AS tmt_hours, 
                        COALESCE(tmt_resource_role, '') AS tmt_resource_role
                    FROM op_time_timetrack
                    WHERE tmt_resource = %s AND tmt_date BETWEEN %s AND %s
                    ORDER BY tmt_customers, tmt_project, tmt_date;
                """
                cursor.execute(query, [resource, start_date_str, end_date_str])

                # Fetch query results
                results = cursor.fetchall()

                # Initialize a dictionary to group data by parent_id
                parent_id_data = {}

                for parent_id, customer, project, date, hours, role in results:
                    key = parent_id  # Group data by parent_id
                    formatted_date = date.strftime('%Y-%m-%d')  # Ensure date format matches week_dates
                    if key not in parent_id_data:
                        parent_id_data[key] = {
                            'parent_id': parent_id,
                            'customer': customer,
                            'project': project,
                            'role': role,
                            'hours_by_date': {}
                        }
                    parent_id_data[key]['hours_by_date'][formatted_date] = hours

                # Prepare the response data
                response_data = []
                for parent_id, data in parent_id_data.items():
                    weekly_hours = [data['hours_by_date'].get(date, 0) for date in week_dates]  # Fill missing days with 0
                    response_data.append({
                        'parent_id': parent_id,  # Include parent_id in the response
                        'customer': data['customer'],
                        'project': data['project'],
                        'role': data['role'],
                        'weekly_hours': weekly_hours
                    })

            return JsonResponse({'status': 'success', 'data': response_data})

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})

    else:
        return JsonResponse({
            'status': 'error',
            'message': 'Invalid HTTP method. Only POST is allowed.'
        })



@csrf_exempt
def get_customer_names(request):
    if request.method == 'GET':
        try:
            with db_cursor() as cursor:
                cursor.execute("SELECT DISTINCT company_name FROM customers")
                customers = cursor.fetchall()

            # Convert fetched tuples into a list of strings
            customer_names = [row[0] for row in customers]

            print(customer_names)

            # Return the list as a JSON response
            return JsonResponse({'status': 'success', 'customer_names': customer_names})

        except Exception as e:
            # Handle database connection errors or query errors
            return JsonResponse({'status': 'error', 'message': str(e)})

    else:
        # Return error if the request method is not GET
        return JsonResponse({'status': 'error', 'message': 'Invalid HTTP method. Only GET is allowed.'})
    


@csrf_exempt
def get_projects_by_company(request):
    if request.method == 'GET':
        # Get the company name from the query parameters
        company_name = request.GET.get('company_name', '')
        if not company_name:
            return JsonResponse({'status': 'error', 'message': 'Company name is required.'})
        
        try:
            with db_cursor() as cursor:
                # Fetch distinct projects for the given company name
                query = """
                    SELECT DISTINCT project FROM customers WHERE company_name = %s;
                """
                cursor.execute(query, [company_name])
                projects = [row[0] for row in cursor.fetchall()]

            return JsonResponse({'status': 'success', 'projects': projects})

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})

    return JsonResponse({'status': 'error', 'message': 'Invalid HTTP method.'})


@csrf_exempt
def delete_time_log(request):
    if request.method == 'DELETE':
        try:
            # Parse the request body
            data = json.loads(request.body)
            parent_id = data.get('parent_id')

            # Validate the payload
            if not parent_id:
                return JsonResponse({'status': 'error', 'message': 'parent_id is required.'}, status=400)

            with db_cursor() as cursor:
                    cursor.execute("DELETE FROM op_time_timetrack WHERE parent_id = %s", [parent_id])
                    rows_deleted = cursor.rowcount

            # If no rows were deleted, return HTTP 204 (No Content)
            if rows_deleted == 0:
                return JsonResponse({}, status=204)  # Return an empty response

            # If rows were deleted, return success
            return JsonResponse({'status': 'success', 'message': 'Row deleted successfully.'})

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

    return JsonResponse({'status': 'error', 'message': 'Invalid HTTP method.'}, status=405)


# Helper function to validate column names
def is_valid_filter(selected_filter: str) -> bool:
    allowed_filters = ["tmt_customers", "tmt_project", "tmt_resource_role"]  # Add all valid columns
    return selected_filter in allowed_filters

# @csrf_exempt
# def search_filter(request):
#     if request.method == 'POST':
#         try:
#             data = json.loads(request.body)
#         except json.JSONDecodeError:
#             return JsonResponse({'status': 'error', 'message': 'Invalid JSON input.'})

#         # Extract input parameters
#         resource = data.get('resource', '').strip()
        
#         # Validate required parameters
#         if not resource :
#             return JsonResponse({
#                 'status': 'error',
#                 'message': 'Resource is required.'
#             })
        
        

#         # Validate filter
#         if not is_valid_filter(selected_filter):
#             return JsonResponse({'status': 'error', 'message': 'Invalid filter name.'})

#         print(f"Selected Filter: {selected_filter}, Search Term: {search_term}")


#         try:
#             # Connect to the database
#             conn = psycopg.connect(
#                 dbname='users',
#                 user='postgres',
#                 password='Aspyr12345!',
#                 host='localhost',
#                 port='5432'
#             )
#             cursor = conn.cursor()

#             # Construct query with dynamic column name
#             query = f"""
#             SELECT tmt_resource, tmt_date, tmt_customers, tmt_project, tmt_resource_role, tmt_hours,tmt_id
#             FROM op_time_timetrack
#             WHERE tmt_resource = %s AND {selected_filter} ILIKE %s;
#             """

#             cursor.execute(query, [resource, f'%{search_term}%'])

#             # Fetch results
#             rows = cursor.fetchall()

#             # Format results
#             results = []
#             for row in rows:
#                 result = {
#                     'tmt_resource': row[0],
#                     'tmt_date': row[1],
#                     'tmt_customer': row[2],
#                     'tmt_project': row[3],
#                     'tmt_role': row[4],
#                     'tmt_hours': row[5],
#                 }
#                 results.append(result)

#             # Close the database connection
#             cursor.close()
#             conn.close()

#             return JsonResponse({'status': 'success', 'data': results})

#         except Exception as e:
#             return JsonResponse({'status': 'error', 'message': f'Error occurred: {str(e)}'})

#     else:
#         return JsonResponse({'status': 'error', 'message': 'Invalid HTTP method. Only POST is allowed.'})


@csrf_exempt
def search_filter(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON input.'})

        # Extract input parameters
        resource = data.get('resource', '').strip()
        from_date = data.get('fromDate', '').strip()
        to_date = data.get('toDate', '').strip()
        tmt_customers = data.get('tmt_customers', '').strip()
        tmt_project = data.get('tmt_project', '').strip()
        tmt_resource_role = data.get('tmt_resource_role', '').strip()

        # Validate required 'resource' field
        if not resource:
            return JsonResponse({'status': 'error', 'message': 'Resource is required.'})

        # Base query to select required fields
        query = """
            SELECT tmt_resource, tmt_date, tmt_customers, tmt_project, tmt_resource_role, tmt_hours
            FROM op_time_timetrack
            WHERE tmt_resource = %s
        """
        query_params = [resource]

        # Add filters for each optional parameter
        if from_date and not to_date:
            # Filter for the specific date if only fromDate is provided
            query += " AND tmt_date = %s"
            query_params.append(from_date)
        elif from_date and to_date:
            # Filter for the date range if both fromDate and toDate are provided
            query += " AND tmt_date >= %s AND tmt_date <= %s"
            query_params.extend([from_date, to_date])

        if tmt_customers:
            query += " AND tmt_customers ILIKE %s"
            query_params.append(f'%{tmt_customers}%')

        if tmt_project:
            query += " AND tmt_project ILIKE %s"
            query_params.append(f'%{tmt_project}%')

        if tmt_resource_role:
            query += " AND tmt_resource_role ILIKE %s"
            query_params.append(f'%{tmt_resource_role}%')

        try:
            with db_cursor() as cursor:

            # Execute the query with dynamic filters
                cursor.execute(query, query_params)

                # Fetch results
                rows = cursor.fetchall()

                # Format results
                results = []
                for row in rows:
                    result = {
                        'tmt_resource': row[0],
                        'tmt_date': row[1],
                        'tmt_customers': row[2],
                        'tmt_project': row[3],
                        'tmt_resource_role': row[4],
                        'tmt_hours': row[5],
                    }
                    results.append(result)


            return JsonResponse({'status': 'success', 'data': results})

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': f'Error occurred: {str(e)}'})

    else:
        return JsonResponse({'status': 'error', 'message': 'Invalid HTTP method. Only POST is allowed.'})

