from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        # Step 1: Create the sequence explicitly
        migrations.RunSQL(
            """
            CREATE SEQUENCE IF NOT EXISTS customers_id_seq
            START 1
            INCREMENT 1;
            """
        ),
        # Step 2: Create the customers table and link the sequence
        migrations.RunSQL(
            """
            CREATE TABLE IF NOT EXISTS public.customers
            (
                id integer NOT NULL DEFAULT nextval('customers_id_seq'::regclass),
                company_name character varying(255) COLLATE pg_catalog."default" NOT NULL,
                project character varying(255) COLLATE pg_catalog."default" NOT NULL,
                CONSTRAINT customers_pkey PRIMARY KEY (company_name, project)
            )
            TABLESPACE pg_default;
            """
        ),
        # Step 3: Ensure the sequence is owned by the id column
        migrations.RunSQL(
            """
            ALTER SEQUENCE customers_id_seq OWNED BY public.customers.id;
            """
        ),
        # Step 4: Set the table ownership (optional but recommended)
        migrations.RunSQL(
            """
            ALTER TABLE IF EXISTS public.customers
                OWNER TO postgres;
            """
        ),
        # Step 5: Create credentials table
        migrations.RunSQL(
            """
            CREATE TABLE IF NOT EXISTS public.credentials
            (
                email character varying(100) COLLATE pg_catalog."default" NOT NULL,
                password character varying(255) COLLATE pg_catalog."default" NOT NULL,
                username character varying(255) COLLATE pg_catalog."default" NOT NULL,
                role character varying(50) COLLATE pg_catalog."default",
                CONSTRAINT credentials_pkey PRIMARY KEY (email, username),
                CONSTRAINT unique_email UNIQUE (email),
                CONSTRAINT unique_username UNIQUE (username)
            )
            TABLESPACE pg_default;

            ALTER TABLE IF EXISTS public.credentials
                OWNER TO postgres;
            """
        ),
        # Step 6: Create op_time_timetrack table
        migrations.RunSQL(
            """
            CREATE TABLE IF NOT EXISTS public.op_time_timetrack
            (
                tmt_id integer NOT NULL GENERATED ALWAYS AS IDENTITY ( INCREMENT 1 START 1 MINVALUE 1 MAXVALUE 2147483647 CACHE 1 ),
                tmt_resource character varying(255) COLLATE pg_catalog."default" NOT NULL,
                tmt_date date NOT NULL,
                tmt_hours smallint,
                tmt_customers character varying(255) COLLATE pg_catalog."default" NOT NULL,
                tmt_project character varying(255) COLLATE pg_catalog."default" NOT NULL,
                tmt_resource_role character varying(50) COLLATE pg_catalog."default" NOT NULL,
                parent_id uuid NOT NULL,
                CONSTRAINT re_da_co_pr_ro PRIMARY KEY (tmt_resource, tmt_date, tmt_customers, tmt_project, tmt_resource_role),
                CONSTRAINT unique_tmt_id UNIQUE (tmt_id)
            )
            TABLESPACE pg_default;

            ALTER TABLE IF EXISTS public.op_time_timetrack
                OWNER TO postgres;
            """
        ),
    ]
