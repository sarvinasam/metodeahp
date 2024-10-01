from model import db, KriteriaAsosiasi, MatriksKriteria, PerbandinganAlternatif, Kriteria, Alternatif

class BackEnd:
    
    def __init__(self, db_session):
        self.db_session = db_session
        self.arrayNilaiPerbandinganKriteria = []
        self.arrayNilaiPerbandinganAlternatif = []

    def get_matrix_kriteria_from_db(self):
        # Fetch all unique criteria IDs from both columns
        criteria_ids = self.db_session.query(KriteriaAsosiasi.kriteria_id_1).union(
            self.db_session.query(KriteriaAsosiasi.kriteria_id_2)
        ).distinct().all()
        criteria_ids = [id[0] for id in criteria_ids]  # Flatten the result
        matrix_size = len(criteria_ids)

        # Initialize the criteria comparison matrix
        self.arrayNilaiPerbandinganKriteria = [[1.0 if i == j else None for j in range(matrix_size)] for i in range(matrix_size)]

        # Populate the criteria comparison matrix
        for record in self.db_session.query(KriteriaAsosiasi).all():
            try:
                kriteria1_id = criteria_ids.index(record.kriteria_id_1)
                kriteria2_id = criteria_ids.index(record.kriteria_id_2)
                
                if kriteria1_id < matrix_size and kriteria2_id < matrix_size:
                    nilai_record = self.db_session.query(MatriksKriteria).filter_by(asosiasi_id=record.id).first()
                    if nilai_record:
                        self.arrayNilaiPerbandinganKriteria[kriteria1_id][kriteria2_id] = nilai_record.nilai
                        self.arrayNilaiPerbandinganKriteria[kriteria2_id][kriteria1_id] = 1 / nilai_record.nilai if nilai_record.nilai != 0 else 0
            except ValueError as e:
                print(f"Error: {e} - Kriteria ID tidak ditemukan dalam criteria_ids")

    def get_matrix_alternatif_from_db(self):
        # Fetch all unique alternative IDs
        alternatif_ids = self.db_session.query(PerbandinganAlternatif.alternatif_id_1).union(
            self.db_session.query(PerbandinganAlternatif.alternatif_id_2)
        ).distinct().all()
        alternatif_ids = [id[0] for id in alternatif_ids]
        alternatif_size = len(alternatif_ids)

        # Fetch all unique kriteria IDs from PerbandinganAlternatif
        criteria_ids = self.db_session.query(PerbandinganAlternatif.kriteria_id).distinct().all()
        criteria_ids = [id[0] for id in criteria_ids]  # Flatten the result
        kriteria_size = len(criteria_ids)

        # Initialize the alternative comparison matrix
        self.arrayNilaiPerbandinganAlternatif = [[0.0 for _ in range(kriteria_size)] for _ in range(alternatif_size)]

        # Populate the alternative comparison matrix based on kriteria_id
        for record in self.db_session.query(PerbandinganAlternatif).all():
            alternatif1_id = alternatif_ids.index(record.alternatif_id_1)
            alternatif2_id = alternatif_ids.index(record.alternatif_id_2)
            kriteria_id = record.kriteria_id

            # Dapatkan indeks kriteria_id
            if kriteria_id in criteria_ids:
                kriteria_idx = criteria_ids.index(kriteria_id)

                if alternatif1_id < alternatif_size and alternatif2_id < alternatif_size and kriteria_idx < kriteria_size:
                    self.arrayNilaiPerbandinganAlternatif[alternatif1_id][kriteria_idx] = record.nilai
                    self.arrayNilaiPerbandinganAlternatif[alternatif2_id][kriteria_idx] = 1 / record.nilai if record.nilai != 0 else 0

    def hitungJumlahNilaiPerbandingan(self, matrix):
        return [sum(row) for row in zip(*matrix)]

    def hitungNilaiEigen(self, matrix, jumlahNilaiPerbandingan):
        return [[value / jumlahNilaiPerbandingan[j] for j, value in enumerate(row)] for row in matrix]

    def hitungJumlahNilaiEigen(self, arrNilaiEigen):
        return [sum(row) for row in arrNilaiEigen]

    def hitungRataEigen(self, arrJumlahNilaiEigen):
        return [total / len(arrJumlahNilaiEigen) for total in arrJumlahNilaiEigen]

    def hitungAHP(self):
        self.get_matrix_kriteria_from_db()  # Get criteria matrix from database
        jumlahNilaiPerbandinganKriteria = self.hitungJumlahNilaiPerbandingan(self.arrayNilaiPerbandinganKriteria)
        arrNilaiEigenKriteria = self.hitungNilaiEigen(self.arrayNilaiPerbandinganKriteria, jumlahNilaiPerbandinganKriteria)
        arrJumlahNilaiEigenKriteria = self.hitungJumlahNilaiEigen(arrNilaiEigenKriteria)
        arrRatarataKriteria = self.hitungRataEigen(arrJumlahNilaiEigenKriteria)
        
        # Get alternative matrix from database
        self.get_matrix_alternatif_from_db()
        jumlahNilaiPerbandinganAlternatif = self.hitungJumlahNilaiPerbandingan(self.arrayNilaiPerbandinganAlternatif)
        arrNilaiEigenAlternatif = self.hitungNilaiEigen(self.arrayNilaiPerbandinganAlternatif, jumlahNilaiPerbandinganAlternatif)

        # Hitung bobot alternatif untuk tiap kriteria
        arrRatarataAlternatif = [[0 for _ in range(len(arrRatarataKriteria))] for _ in range(len(arrNilaiEigenAlternatif))]

        for alternatif_idx in range(len(arrNilaiEigenAlternatif)):
            for kriteria_idx in range(len(arrRatarataKriteria)):
                # Ambil nilai eigen alternatif untuk kriteria ini
                arrRatarataAlternatif[alternatif_idx][kriteria_idx] = arrNilaiEigenAlternatif[alternatif_idx][kriteria_idx]

        # Normalisasi bobot alternatif
        for kriteria_idx in range(len(arrRatarataKriteria)):
            total = sum(arrRatarataAlternatif[alt_idx][kriteria_idx] for alt_idx in range(len(arrRatarataAlternatif)))
            if total > 0:
                for alt_idx in range(len(arrRatarataAlternatif)):
                    arrRatarataAlternatif[alt_idx][kriteria_idx] /= total

        print("arrRatarataAlternatif:", arrRatarataAlternatif)

        return arrRatarataKriteria, arrRatarataAlternatif