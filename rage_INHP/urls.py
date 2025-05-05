from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.shortcuts import redirect
from django.urls import path, include
from django_unicorn import views

from rage.models import RendezVousVaccination
from rage.views import CADashborad, DistrictDashborad, RegionDashborad, NationalDashborad, PatientListView, \
    PatientDetailView, PatientUpdateView, PatientDeleteView, \
    AnimalListView, AnimalDetailView, AnimalUpdateView, AnimalDeleteView, \
    VaccinationListView, VaccinationDetailView, VaccinationDeleteView, VaccinationUpdateView, PatientCreateView, \
    ajouter_symptome, \
    RendezVousListView, RendezVousDetailView, vacciner, FactureListView, effectuer_paiement, DeclarationTemplate, \
    PreExpositionListView, PreExpositionCreateView, PreExpositionDetailView, PreExpositionUpdateView, \
    PreExpositionDeleteView, PostExpositionListView, PostExpositionCreateView, PostExpositionDetailView, \
    PostExpositionUpdateView, PostExpositionDeleteView, fichePreExpoPDF, get_communes, RageNotificationCreateView, \
    patients_geojson, fichePostExpoPDF, RageHumaineNotificationListView, RageHumaineNotificationDetailView, \
    RageHumaineNotificationUpdateView, RageHumaineNotificationDeleteView, ajouter_mapi, synchroniser_patients_mpi, \
    attestation_vaccination, get_lots_by_vaccin, commune_autocomplete, VaccinCreateView, VaccinDetailView, \
    VaccinUpdateView, LotVaccinCreateView, LotVaccinListView, LotVaccinDetailView, LotVaccinUpdateView, VaccinListView, \
    EmployeeUserListView, EmployeeUserCreateView, EmployeeUserDetailView, EmployeeUserUpdateView, \
    EmployeeUserDeleteView, CentreAntirabiqueListView, CentreAntirabiqueCreateView, CentreAntirabiqueDetailView, \
    CentreAntirabiqueUpdateView, CentreAntirabiqueDeleteView, permission_denied_view, GenerateVaccinationCertificatePDF, \
    InjectionImmunoglobulineCreateView, add_injection_immunoglobuline, generate_avis_surveillance, CartographieView, \
    CartographieDataView

urlpatterns = [
                  path('admin/', admin.site.urls),
                  path('accounts/', include('allauth.urls')),
                  # path('accounts/signup/', lambda request: redirect('/')),
                  path('patients_geojson/', patients_geojson, name='patients_geojson'),
                  path('403/', permission_denied_view, name='permission_denied'),

                  path('', CADashborad.as_view(), name='home'),
                  path('cartographie/', CartographieView.as_view(), name='cartographie'),
                  path('cartographie/data/', CartographieDataView.as_view(), name='cartographie_data'),

                  path('DistrictSanitaire/', DistrictDashborad.as_view(), name='district'),
                  path('Regional/', RegionDashborad.as_view(), name='regional'),
                  path('National/', NationalDashborad.as_view(), name='national'),
                  path('unicorn/', views.message, name='unicorn'),
                  path('unicorn/', include('django_unicorn.urls', namespace='django_unicorn')),
                  path('synchroniser-mpi/', synchroniser_patients_mpi, name='synchroniser_patients_mpi'),

                  #------------------------------------ URL des actions
                  path('declaration/', DeclarationTemplate.as_view(), name='declaration_new'),
                  path('vaccination/<int:pk>/certificat/', GenerateVaccinationCertificatePDF.as_view(),
                       name='vaccination_certificate'),

                  path('patients/', PatientListView.as_view(), name='patient_list'),
                  path('patients/add/', PatientCreateView.as_view(), name='patient_create'),
                  path('patients/<int:pk>/', PatientDetailView.as_view(), name='patient_detail'),
                  path('patients/<int:pk>/update/', PatientUpdateView.as_view(), name='patient_update'),
                  path('patients/<int:pk>/delete/', PatientDeleteView.as_view(), name='patient_delete'),

                  path("injection/add/<int:patient_id>/", add_injection_immunoglobuline, name="injection_immuno_add"),

                  # path('expositions/', ExpositionListView.as_view(), name='exposition_list'),
                  # path('expositions/<int:pk>/', ExpositionDetailView.as_view(), name='exposition_detail'),
                  # path('expositions/create', ExpositionCreateView.as_view(), name='exposition_create'),
                  # path('expositions/<int:pk>/update/', ExpositionUpdateView.as_view(), name='exposition_update'),
                  # path('expositions/<int:pk>/delete/', ExpositionDeleteView.as_view(), name='exposition_delete'),
                  path('preexposition/<int:pk>/pdf/', fichePreExpoPDF, name='fichepreexpoPDF'),
                  path('postexposition/<int:pk>/pdf/', fichePostExpoPDF, name='fichepostexpoPDF'),

                  path('preexposition/', PreExpositionListView.as_view(), name='preexposition_list'),
                  path('preexposition/add/', PreExpositionCreateView.as_view(), name='preexposition_add'),
                  path('preexposition/<int:pk>/', PreExpositionDetailView.as_view(), name='preexposition_detail'),
                  path('preexposition/<int:pk>/edit/', PreExpositionUpdateView.as_view(), name='preexposition_edit'),
                  path('preexposition/<int:pk>/delete/', PreExpositionDeleteView.as_view(),
                       name='preexposition_delete'),
                  path('api/communes/', get_communes, name='get_communes'),

                  path('postexposition/', PostExpositionListView.as_view(), name='postexposition_list'),
                  path('postexposition/add/', PostExpositionCreateView.as_view(), name='postexposition_add'),
                  path('postexposition/<int:pk>/', PostExpositionDetailView.as_view(), name='postexposition_detail'),
                  path('postexposition/<int:pk>/edit/', PostExpositionUpdateView.as_view(), name='postexposition_edit'),
                  path('postexposition/<int:pk>/delete/', PostExpositionDeleteView.as_view(),
                       name='postexposition_delete'),
                  # urls.py
                  path('exposition/<int:exposition_id>/avis-surveillance/', generate_avis_surveillance,
                       name='generate_avis_surveillance'),

                  path('notification/', RageHumaineNotificationListView.as_view(), name='notification_rage_liste'),
                  path('notification/add/', RageNotificationCreateView.as_view(), name='notification_rage_add'),

                  path('notification/details/<int:pk>/', RageHumaineNotificationDetailView.as_view(),
                       name='rage_notification_detail'),
                  path('notification/update/<int:pk>/', RageHumaineNotificationUpdateView.as_view(),
                       name='rage_notification_update'),
                  path('notification/delete/<int:pk>/', RageHumaineNotificationDeleteView.as_view(),
                       name='rage_notification_delete'),

                  # path('ajout-protocole/<int:exposition_id>', ajouterProtocole, name='ajout-protocole-expo'),
                  path('symptomes/ajouter/', ajouter_symptome, name='ajouter_symptome'),
                  # path('echantillons/ajouter/<int:exposition_id>/', ajouter_echantillon, name='ajouter_echantillon'),

                  path('animaux/', AnimalListView.as_view(), name='animal_list'),
                  path('animaux/<int:pk>/', AnimalDetailView.as_view(), name='animal_detail'),
                  path('animaux/<int:pk>/update/', AnimalUpdateView.as_view(), name='animal_update'),
                  path('animaux/<int:pk>/delete/', AnimalDeleteView.as_view(), name='animal_delete'),

                  path('rendez-vous/', RendezVousListView.as_view(), name='vaccin-rdv-list'),
                  path('rendez-vous/detail/<int:pk>', RendezVousDetailView.as_view(), name='detail_rendez_vous'),

                  path('factures/', FactureListView.as_view(), name='liste_factures'),
                  path('facture/<int:facture_id>/paiement/', effectuer_paiement, name='effectuer_paiement'),

                  path('mapi/ajouter/<int:vaccination_id>/', ajouter_mapi, name='ajouter_mapi'),

                  # path('api/lots/', lots_par_vaccin, name='lots_par_vaccin'),
                  path('ajax/get-lots/', get_lots_by_vaccin, name='get_lots_by_vaccin'),

                  path('vacciner/<int:rendez_vous_id>/', vacciner, name='vacciner'),
                  path('vaccination/<int:vaccination_id>/attestation/', attestation_vaccination,
                       name='attestation_vaccination'),
                  path('vaccinations/', VaccinationListView.as_view(), name='vaccination_list'),
                  path('vaccinations/<int:pk>/', VaccinationDetailView.as_view(), name='vaccination_detail'),
                  path('vaccinations/<int:pk>/update/', VaccinationUpdateView.as_view(), name='vaccination_update'),
                  path('vaccinations/<int:pk>/delete/', VaccinationDeleteView.as_view(), name='vaccination_delete'),

                  path('ajax/communes/', commune_autocomplete, name='commune_autocomplete'),

                  #------------Parametres -----------------------------#

                  path('vaccins/', VaccinListView.as_view(), name='vaccin_list'),
                  path('vaccins/ajouter/', VaccinCreateView.as_view(), name='vaccin_create'),
                  path('vaccins/<int:pk>/', VaccinDetailView.as_view(), name='vaccin_detail'),
                  path('vaccins/<int:pk>/modifier/', VaccinUpdateView.as_view(), name='vaccin_update'),

                  # Lots de vaccins URLs
                  path('lots/', LotVaccinListView.as_view(), name='lot_vaccin_list'),
                  path('lots/ajouter/', LotVaccinCreateView.as_view(), name='lot_vaccin_create'),
                  path('lots/<int:pk>/', LotVaccinDetailView.as_view(), name='lot_vaccin_detail'),
                  path('lots/<int:pk>/modifier/', LotVaccinUpdateView.as_view(), name='lot_vaccin_update'),

                  #--------------users-----------------

                  path('utilisateurs/', EmployeeUserListView.as_view(), name='employeeuser_list'),
                  path('utilisateurs/ajouter/', EmployeeUserCreateView.as_view(), name='employeeuser_create'),
                  path('utilisateurs/<int:pk>/', EmployeeUserDetailView.as_view(), name='employeeuser_detail'),
                  path('utilisateurs/<int:pk>/modifier/', EmployeeUserUpdateView.as_view(), name='employeeuser_update'),
                  path('utilisateurs/<int:pk>/supprimer/', EmployeeUserDeleteView.as_view(),
                       name='employeeuser_delete'),

                  # URLs pour les centres
                  path('centres/', CentreAntirabiqueListView.as_view(), name='centreantirabique_list'),
                  path('centres/ajouter/', CentreAntirabiqueCreateView.as_view(), name='centreantirabique_create'),
                  path('centres/<int:pk>/', CentreAntirabiqueDetailView.as_view(), name='centreantirabique_detail'),
                  path('centres/<int:pk>/modifier/', CentreAntirabiqueUpdateView.as_view(),
                       name='centreantirabique_update'),
                  path('centres/<int:pk>/supprimer/', CentreAntirabiqueDeleteView.as_view(),
                       name='centreantirabique_delete'),

                  path('injection/add/', InjectionImmunoglobulineCreateView.as_view(), name='injection_immuno_add'),

                  #------------fonctions conext
                  # path('exposition/<int:exposition_id>/pdf/', generate_exposition_pdf, name='generate_exposition_pdf'),

              ] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
