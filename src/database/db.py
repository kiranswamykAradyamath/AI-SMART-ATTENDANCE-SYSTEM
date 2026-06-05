import bcrypt
import httpx

from src.database.config import supabase


class DatabaseConnectionError(RuntimeError):
    pass

def hash_pass(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def check_pass(password, hash_password):
    return bcrypt.checkpw(password.encode(), hash_password.encode())


def check_teacher_exists(username):
    # check for unique username, returns false when username is already taken 
    response = supabase.table("teachers").select("username").eq("username", username).execute()
    return len(response.data) > 0


def create_teacher(username, password, name ):

    data = { "username": username, "password": hash_pass(password), "name": name }
    response = supabase.table("teachers").insert(data).execute()
    return response.data

def teacher_login(username,password):
    response = supabase.table("teachers").select("*").eq("username",username).execute()

    if response.data:
        teacher = response.data[0]
        if check_pass(password, teacher['password']):
            return teacher

        return None
    

def get_all_students():
    try:
        response = supabase.table("students").select("*").execute()
    except httpx.ConnectError as exc:
        raise DatabaseConnectionError(
            "Could not connect to Supabase. Check your internet connection, DNS, "
            "and SUPABASE_URL in .streamlit/secrets.toml."
        ) from exc
    return response.data

def create_student(new_name, face_embedding, voice_embedding):
    data = {
        "name": new_name,
        "face_embedding": face_embedding,
        "voice_embedding": voice_embedding
    }
    response = supabase.table("students").insert(data).execute()
    return response.data



def create_subject(subject_code, name, section, teacher_id):
    data = {
        "subject_code": subject_code,
        "name": name,
        "section": section,
        "teacher_id": teacher_id
    }
    response = supabase.table("subjects").insert(data).execute()
    return response.data

def get_teacher_subjects(teacher_id):
    response = supabase.table("subjects").select("*, subject_students(count), attendance_logs(timestamp)").eq("teacher_id", teacher_id).execute()
    subject = response.data

    for sub in subject:
        sub['total_students'] = sub.get('subject_students', [{}])[0].get('count', 0) if sub.get('subject_students') else 0
        attendance = sub.get('attendance_logs',[])
        unique_sessions = len(set(log['timestamp'] for log in attendance))
        
        sub['total_sessions'] = unique_sessions
        sub['total_classes'] = unique_sessions

        

        sub.pop('subject_students', None)
        sub.pop('attendance_logs', None)


    return response.data

def enroll_student_to_subject(student_id, subject_id):
    data = {
        "student_id": student_id,
        "subject_id": subject_id
    }
    response = supabase.table("subject_students").insert(data).execute()
    return response.data

def unenroll_student_to_subject(student_id, subject_id):
   
    response = supabase.table("subject_students").delete().eq("student_id", student_id).eq("subject_id", subject_id).execute()
    return response.data

def get_student_subjects(student_id):
    response = supabase.table("subject_students").select('*, subjects(*)').eq("student_id", student_id).execute()
    return response.data

def get_subject_students(subject_id):
    response = supabase.table("subject_students").select("*, students(*)").eq("subject_id", subject_id).execute()
    return response.data

def get_student_attendance(student_id):
    response = supabase.table("attendance_logs").select("*, subjects(*)").eq("student_id", student_id).execute()
    return response.data


def create_attendance(logs):
    response = supabase.table('attendance_logs').insert(logs).execute()
    return response

def get_attendance_for_teacher(teacher_id):
    response = supabase.table('attendance_logs').select("*, subjects!inner(*)").eq('subjects.teacher_id', teacher_id).execute()
    return response.data
