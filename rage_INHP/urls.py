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
    attestation_vaccination, get_lots_by_vaccin

urlpatterns = [
                  path('admin/', admin.site.urls),
                  path('accounts/', include('allauth.urls')),
                  # path('accounts/signup/', lambda request: redirect('/')),
                  path('patients_geojson/', patients_geojson, name='patients_geojson'),

                  path('', CADashborad.as_view(), name='home'),
                  path('DistrictSanitaire/', DistrictDashborad.as_view(), name='district'),
                  path('Regional/', RegionDashborad.as_view(), name='regional'),
                  path('National/', NationalDashborad.as_view(), name='national'),
                  path('unicorn/', views.message, name='unicorn'),
                  path('unicorn/', include('django_unicorn.urls', namespace='django_unicorn')),
                  path('synchroniser-mpi/', synchroniser_patients_mpi, name='synchroniser_patients_mpi'),

                  #------------------------------------ URL des actions
                  path('declaration/', DeclarationTemplate.as_view(), name='declaration_new'),

                  path('patients/', PatientListView.as_view(), name='patient_list'),
                  path('patients/add/', PatientCreateView.as_view(), name='patient_create'),
                  path('patients/<int:pk>/', PatientDetailView.as_view(), name='patient_detail'),
                  path('patients/<int:pk>/update/', PatientUpdateView.as_view(), name='patient_update'),
                  path('patients/<int:pk>/delete/', PatientDeleteView.as_view(), name='patient_delete'),

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

                  path('notification/', RageHumaineNotificationListView.as_view(), name='notification_rage_liste'),
                  path('notification/add/', RageNotificationCreateView.as_view(), name='notification_rage_add'),

                  path('notification/<int:pk>/', RageHumaineNotificationDetailView.as_view(),
                       name='rage_notification_detail'),
                  path('notification/<int:pk>/', RageHumaineNotificationUpdateView.as_view(),
                       name='rage_notification_update'),
                  path('notification/<int:pk>/', RageHumaineNotificationDeleteView.as_view(),
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

                  #------------fonctions conext
                  # path('exposition/<int:exposition_id>/pdf/', generate_exposition_pdf, name='generate_exposition_pdf'),

              ] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
