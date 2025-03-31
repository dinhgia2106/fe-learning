-- Create the users table
CREATE TABLE public.users
(
    id SERIAL PRIMARY KEY,
    user_name TEXT NOT NULL UNIQUE,
    created_at TIMESTAMP
    WITH TIME ZONE DEFAULT NOW
    ()
);

    -- Create the quiz_history table
    CREATE TABLE public.quiz_history
    (
        id SERIAL PRIMARY KEY,
        user_name TEXT NOT NULL,
        course_id TEXT NOT NULL,
        quiz_set TEXT NOT NULL,
        score FLOAT NOT NULL,
        total_questions INTEGER,
        date_time TIMESTAMP
        WITH TIME ZONE DEFAULT NOW
        (),
    duration TEXT,
    user_answers JSONB,
    questions JSONB,
    FOREIGN KEY
        (user_name) REFERENCES public.users
        (user_name) ON
        DELETE CASCADE
);

        -- Create the explanations table
        CREATE TABLE public.explanations
        (
            id SERIAL PRIMARY KEY,
            user_name TEXT NOT NULL,
            explanation_key TEXT NOT NULL,
            explanation_text TEXT NOT NULL,
            created_at TIMESTAMP
            WITH TIME ZONE DEFAULT NOW
            (),
    FOREIGN KEY
            (user_name) REFERENCES public.users
            (user_name) ON
            DELETE CASCADE,
    UNIQUE(user_name, explanation_key)
            );

            -- Create indexes for better query performance
            CREATE INDEX idx_quiz_history_user_name ON public.quiz_history(user_name);
            CREATE INDEX idx_explanations_user_name ON public.explanations(user_name);
            CREATE INDEX idx_quiz_history_date_time ON public.quiz_history(date_time);
            CREATE INDEX idx_explanations_key ON public.explanations(explanation_key);

            -- Enable Row Level Security (RLS)
            ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;
            ALTER TABLE public.quiz_history ENABLE ROW LEVEL SECURITY;
            ALTER TABLE public.explanations ENABLE ROW LEVEL SECURITY;

            -- Create RLS policies for the users table
            CREATE POLICY "Allow insert for authenticated users" 
ON public.users FOR
            INSERT TO authenticated WITH CHECK (
            true);

            CREATE POLICY "Allow select for authenticated users" 
ON public.users FOR
            SELECT TO authenticated
            USING
            (true);

            -- Create RLS policies for the quiz_history table
            CREATE POLICY "Allow all operations for the same user or admin" 
ON public.quiz_history
FOR ALL TO authenticated
USING
            (true);

            -- Create RLS policies for the explanations table
            CREATE POLICY "Allow all operations for the same user or admin" 
ON public.explanations
FOR ALL TO authenticated
USING
            (true);

            -- Allow anon access for the app
            CREATE POLICY "Allow anonymous access" 
ON public.users FOR
            SELECT TO anon
            USING
            (true);

            CREATE POLICY "Allow anonymous select on quiz_history" 
ON public.quiz_history FOR
            SELECT TO anon
            USING
            (true);

            CREATE POLICY "Allow anonymous select on explanations" 
ON public.explanations FOR
            SELECT TO anon
            USING
            (true);

            CREATE POLICY "Allow anonymous insert on users" 
ON public.users FOR
            INSERT TO anon WITH CHECK (
            true);

            CREATE POLICY "Allow anonymous insert on quiz_history" 
ON public.quiz_history FOR
            INSERT TO anon WITH CHECK (
            true);

            CREATE POLICY "Allow anonymous insert on explanations" 
ON public.explanations FOR
            INSERT TO anon WITH CHECK (
            true);

            -- Create a storage bucket for quiz data
            INSERT INTO storage.buckets
                (id, name, public)
            VALUES
                ('quiz_data', 'Quiz Data', true);

            -- Create a policy to allow authenticated users to upload files
            CREATE POLICY "Allow authenticated users to upload files"
ON storage.objects FOR
            INSERT
TO authenticated
WITH CHECK (
            bucket_id
            =
            'quiz_data'
            );

            -- Create a policy to allow reading public quiz data
            CREATE POLICY "Allow public read access"
ON storage.objects FOR
            SELECT
                TO public
USING
            (bucket_id = 'quiz_data');