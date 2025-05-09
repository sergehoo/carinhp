import requests
from django.conf import settings

from rage_INHP.MPIClient import MPIClient


def synchroniser_avec_mpi(patient_instance):
    mpi_client = MPIClient(
        username="rageuser",
        api_key=settings.MPI_API_KEY,
        mpi_base_url="https://mpici.com"
    )

    patient_data = {
        "nom": patient_instance.nom,
        "prenoms": patient_instance.prenoms,
        "date_naissance": patient_instance.date_naissance.isoformat(),
        "contact": str(patient_instance.contact) if patient_instance.contact else None,
        "sexe": patient_instance.sexe,
        "num_cmu": patient_instance.num_cmu,
        "cni_num": patient_instance.cni_num,
        "cni_nni": patient_instance.cni_nni,
        "profession": patient_instance.secteur_activite,
        "niveau_etude": patient_instance.niveau_etude,
        # "quartier": patient_instance.quartier,
        # "village": patient_instance.village,
    }

    mpi_response = mpi_client.synchroniser_patient(patient_data)
    return mpi_response.get("upi")
# def synchroniser_avec_mpi(patient_instance):
#     mpi_url = "http://127.0.0.1:8001/mpi/patients/"  # URL du create/update patient MPI
#     token_url = "http://127.0.0.1:8001/api/token/"
#
#     platform_username = "rage"  # doit correspondre au nom d’utilisateur lié à Platform
#     platform_api_key = settings.MPI_API_KEY  # stocké dans .env ou settings sécurisés
#
#     # Étape 1 - Authentifier pour obtenir token
#     response = requests.post(token_url, json={
#         "username": platform_username,
#         "api_key": platform_api_key
#     })
#     if response.status_code != 200:
#         raise Exception("Échec de l'authentification MPI")
#
#     token = response.json()["access"]
#
#     # Étape 2 - Envoi des données du patient
#     payload = {
#         "nom": patient_instance.nom,
#         "prenoms": patient_instance.prenoms,
#         "date_naissance": str(patient_instance.date_naissance),
#         "contact": patient_instance.contact,
#         "sexe": patient_instance.sexe,
#     }
#
#     response = requests.post(mpi_url, json=payload, headers={
#         "Authorization": f"Bearer {token}",
#         "Content-Type": "application/json"
#     })
#
#     if response.status_code not in [200, 201]:
#         raise Exception(f"Erreur de communication avec MPI: {response.content}")
#
#     data = response.json()
#     return data.get("upi")