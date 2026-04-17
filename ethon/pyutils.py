import os
import pathlib
import shutil


# ================= SAFE RENAME =================

def rename(source, output, overwrite=True):
    """
    Rename file dengan handling error & overwrite optional
    """
    try:
        if not os.path.exists(source):
            raise FileNotFoundError(f"Source tidak ditemukan: {source}")

        if os.path.exists(output):
            if overwrite:
                os.remove(output)
            else:
                raise FileExistsError(f"Target sudah ada: {output}")

        os.rename(source, output)
        return output

    except Exception as e:
        print("Rename error:", e)
        return None


# ================= GET FILE EXTENSION =================

def file_extension(file_path):
    """
    Ambil ekstensi file (.mp4, .mkv, dll)
    """
    try:
        return pathlib.Path(file_path).suffix.lower()
    except Exception:
        return ""


# ================= QUEUE LENGTH CHECK =================

def Q_length(List, limit):
    """
    Cek panjang queue
    return:
        - 'FULL' kalau melebihi limit
        - jumlah item kalau masih aman
    """
    try:
        length = len(List)

        # FIX: sebelumnya salah logika (limit + 1)
        if length >= int(limit):
            return "FULL"

        return length

    except Exception:
        return 0