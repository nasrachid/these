#pour la page de presentation 
import secrets
from tkinter import Message
from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.contrib.auth.hashers import make_password


from .forms import CommentaireForm, DoctorantInscriptionForm
from .models import DemandeInscription, Utilisateur
import random, string


def demande_inscription(request):
    if request.method == 'POST':
        form = DoctorantInscriptionForm(request.POST)
        if form.is_valid():
            form.save()  # Si tu as un modèle, tu peux utiliser form.save() ici.
            # Envoie un message de succès
            messages.success(request, 'Votre demande a été envoyée avec succès.')
            return render(request, 'Presentation/inscription_doctorant.html', {'form': form})
        else:
            # Envoie un message d'erreur si le formulaire n'est pas valide
            messages.error(request, 'Il y a des erreurs dans votre demande. Veuillez vérifier les informations.')
    else:
        form = DoctorantInscriptionForm()

    return render(request, 'Presentation/inscription_doctorant.html', {'form': form})

# Cette vue serait appelée manuellement par un admin (ou via un bouton)
from django.core.mail import send_mail
from django.http import HttpResponse
from django.contrib.auth.hashers import make_password
import random, string
from .models import DemandeInscription, Utilisateur

def valider_inscription_doctorant(demande_id):
    try:
        demande = DemandeInscription.objects.get(id=demande_id)
    except DemandeInscription.DoesNotExist:
        return HttpResponse("Demande d'inscription introuvable.")

    mot_de_passe = ''.join(random.choices(string.ascii_letters + string.digits, k=8))

    # Création de l'utilisateur
    utilisateur = Utilisateur.objects.create(
        username=demande.email,
        email=demande.email,
        nom=demande.nom_complet,
        role='doctorant',
        promotion=demande.promotion,
        adresse=demande.adresse,
        date_naissance=demande.date_naissance,
        password=make_password(mot_de_passe),
    )

    # Tentative d'envoi de l'email
    try:
        send_mail(
            'Identifiants de connexion',
            f'Bonjour {utilisateur.nom},\n\nVoici vos identifiants :\nEmail : {utilisateur.email}\nMot de passe : {mot_de_passe}',
            'nasrarachid97@gmail.com',  # Assure-toi que c'est le bon email
            [utilisateur.email],  # L'email du destinataire
            fail_silently=False,
        )
        print("✅ Email envoyé à :", utilisateur.email)
        message = "L'utilisateur a été créé et l'email envoyé avec succès."

    except Exception as e:
        print("❌ Erreur lors de l’envoi de l’email :", e)
        message = f"Erreur lors de l'envoi de l'email : {e}"

    # Suppression de la demande une fois l'inscription validée
    demande.delete()
    
    return HttpResponse(message)






from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import ConnexionForm  # si ce n'est pas déjà importé

def connexion(request):
    if request.method == 'POST':
        form = ConnexionForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']

            user = authenticate(request, username=username, password=password)
            if user is not None:
                print("Utilisateur authentifié :", user.username)
                print("Rôle :", user.role)

                login(request, user)

                # 🔐 Gestion de la case à cocher "Se souvenir de moi"
                remember = request.POST.get('remember')  # récupère 'on' si coché
                if not remember:
                    request.session.set_expiry(0)  # expire à la fermeture du navigateur
                else:
                    request.session.set_expiry(1209600)  # 2 semaines

                # Redirection selon le rôle
                if user.role == 'doctorant':
                    print("Redirection vers profil_et_these")
                    return redirect('liste_soutenances')
                elif user.role == 'professeur':
                    print("Redirection vers page_rapporteur")
                    return redirect('page_rapporteur')
                elif user.role == 'comite':
                    print("Redirection vers tableau_theses_comite")
                    return redirect('tableau_theses_comite')
                else:
                    print("Rôle non reconnu")
                    messages.error(request, "Rôle non reconnu.")
            else:
                print("Authentification échouée")
                messages.error(request, "Nom d'utilisateur ou mot de passe incorrect.")
        else:
            print("Formulaire invalide")
            messages.error(request, "Veuillez remplir tous les champs.")
    else:
        form = ConnexionForm()

    return render(request, 'Presentation/connexion.html', {'form': form})


def presentation(request):
    return render(request, 'Presentation/presentation.html')

def apropo(request):
    return render(request, 'Presentation/apropo.html')




from django.shortcuts import render
from django.contrib import messages
from .models import HistoriqueAction

def accueil_etudiant(request):
    if request.user.is_authenticated and not request.user.password_changed:
        messages.warning(request, "⚠️ Pour des raisons de sécurité, pensez à changer votre mot de passe régulièrement.\nVous pouvez le faire via le menu latéral dans 'Changer le mot de passe'.")

    historique = HistoriqueAction.objects.all().order_by('-date_action')[:10]
    return render(request, 'Presentation/liste_soutenances.html', {'historique': historique})


from django.contrib.auth.decorators import login_required

@login_required
def profil_etudiant(request):
    return render(request, 'presentation/profil.html')



from django.contrib.auth.decorators import login_required
from .models import These, Notification, HistoriqueAction
from django.shortcuts import render, redirect
from django.contrib import messages

@login_required
def copie_zero(request):
    utilisateur = request.user

    # Vérifie s'il a déjà soumis une thèse
    these_deja_soumise = These.objects.filter(utilisateur=utilisateur).exists()

    if request.method == 'POST':
        if these_deja_soumise:
            messages.error(request, "Vous avez déjà soumis votre thèse. Vous ne pouvez pas en soumettre une autre.")
            return redirect('copie_zero')

        # Récupération des données du formulaire
        titre = request.POST.get('titre')
        domaine = request.POST.get('domaine')
        description = request.POST.get('description')
        motivation = request.POST.get('motivation')
        encadreur = request.POST.get('encadreur')
        fichier = request.FILES.get('fichier', None)

        # Création de la thèse
        these = These.objects.create(
            utilisateur=utilisateur,
            titre=titre,
            domaine=domaine,
            description=description,
            motivation=motivation,
            encadreur=encadreur,
            fichier=fichier
        )

        # Historique de l'action
        HistoriqueAction.objects.create(
            utilisateur=utilisateur,
            action=f"Soumission de la thèse '{titre}'"
        )

        # Création de la notification
        Notification.objects.create(
            utilisateur=utilisateur,
            titre="Soumission réussie",
            message=f"Votre thèse '{titre}' a bien été soumise pour évaluation.",
            
        )
        messages.success(request, f"Votre thèse '{titre}' a bien été soumise sous la direction de {encadreur}.")

        return redirect('copie_zero')

    # Envoi de l'info au template pour désactiver le bouton
    return render(request, 'presentation/copie_zero.html', {
        'these_deja_soumise': these_deja_soumise
    })

from django.contrib import messages
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from .models import These, RapportIntermediaire, Notification


@login_required
def rapport_intermediaire(request):
    # Trouver la thèse approuvée, sans rapport intermédiaire encore soumis
    these = These.objects.filter(
    utilisateur=request.user,
    statut='Approuvé',
    approuve_par_comite=True
).exclude(
    rapports_intermediaires__isnull=False
).order_by('-date_soumission').first()

    is_approved = these is not None

    # Si la méthode est POST mais aucune thèse valide n’a été trouvée
    if request.method == 'POST' and not these:
        messages.error(request, "Aucune thèse approuvée trouvée ou vous avez déjà soumis un rapport.")
        return redirect('rapport_intermediaire')

    if request.method == 'POST':
        fichier = request.FILES.get('fichier', None)

        if not fichier:
            messages.error(request, "Veuillez télécharger un fichier pour le rapport intermédiaire.")
        else:
            # Créer le rapport intermédiaire
            RapportIntermediaire.objects.create(
                these=these,
                fichier=fichier
            )

            Notification.objects.create(
                utilisateur=request.user,
                message="Votre rapport intermédiaire a bien été soumis.",
                lu=False
            )

            messages.success(request, "Votre rapport intermédiaire a bien été soumis !")
            return redirect('rapport_intermediaire')

    return render(request, 'presentation/rapport_intermediaire.html', {
        'these': these,
        'is_approved': is_approved,
        'rapport_existant': RapportIntermediaire.objects.filter(these=these).first() if these else None
    })


from django.contrib import messages
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import These, RapportFinal
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import These, RapportFinal

@login_required
def rapport_final(request):
    utilisateur = request.user
    these = These.objects.filter(utilisateur=utilisateur).first()

    if not these:
        messages.error(request, "Aucune thèse trouvée. Veuillez d'abord soumettre le rapport_intermediaire.")
        return redirect('rapport_intermediaire')  # Redirige l'utilisateur pour qu'il soumette d'abord la copie 0

    rapport_intermediaire_approve = (
        hasattr(these, 'rapportintermediaire') and these.rapportintermediaire.approuve_par_comite
    )

    if request.method == 'POST':
        if not rapport_intermediaire_approve:
            messages.error(request, "Le rapport intermédiaire n’est pas encore approuvé. Vous ne pouvez pas soumettre le rapport final.")
            return redirect('rapport_final')

        titre = request.POST.get('titre')
        fichier = request.FILES.get('fichier')

        if not titre or not fichier:
            messages.error(request, "Veuillez fournir un titre et un fichier.")
        else:
            RapportFinal.objects.create(
                these=these,
                titre=titre,
                fichier=fichier
            )
            messages.success(request, "Votre rapport final a bien été soumis !")
            return redirect('rapport_final')

    return render(request, 'presentation/rapport_final.html', {
        'these': these,
        'is_approved': rapport_intermediaire_approve  # Cette variable détermine l'état du formulaire
    })



from django.http import JsonResponse
from .models import These
import re
import unicodedata
from rapidfuzz import fuzz

# Mots à ignorer
STOPWORDS = {"de", "la", "le", "et", "les", "du", "des", "un", "une", "en", "au", "aux",
             "avec", "pour", "par", "dans", "sur", "qui", "que", "quoi", "quand", "comme", "cest"}

def normaliser_texte(texte):
    """Nettoyage du texte : minuscules, sans accents, sans ponctuation, sans stopwords"""
    if not texte:
        return ""
    
    texte = unicodedata.normalize('NFD', texte).encode('ascii', 'ignore').decode('utf-8')
    texte = re.sub(r'[^\w\s]', ' ', texte.lower())
    mots = [mot for mot in texte.split() if mot not in STOPWORDS and len(mot) > 2]
    return ' '.join(mots)

def verifier_titre(request):
    titre = request.GET.get('titre', '').strip()
    if not titre:
        return JsonResponse({'existe': False, 'message': 'Veuillez fournir un titre.'})

    titre_normalise = normaliser_texte(titre)
    if not titre_normalise:
        return JsonResponse({'existe': False, 'message': 'Titre trop court après nettoyage.'})

    titres_existants = These.objects.values_list('titre', flat=True)

    meilleure_similarite = 0
    meilleur_titre = None

    for titre_existant in titres_existants:
        titre_existant_normalise = normaliser_texte(titre_existant)
        if not titre_existant_normalise:
            continue

        # Utilisation de token_set_ratio pour ignorer l'ordre des mots
        similarite = fuzz.token_set_ratio(titre_normalise, titre_existant_normalise)

        if similarite > meilleure_similarite:
            meilleure_similarite = similarite
            meilleur_titre = titre_existant

        if similarite >= 85:
            return JsonResponse({
                'existe': True,
                'titre_existant': titre_existant,
                'similarite': similarite,
                'message': 'Ce titre ressemble beaucoup à un titre existant.'
            })

    if meilleure_similarite >= 70:
        return JsonResponse({
            'existe': True,
            'titre_existant': meilleur_titre,
            'similarite': meilleure_similarite,
            'message': f'Titre similaire détecté ({meilleure_similarite}%).'
        })

    return JsonResponse({
        'existe': False,
        'message': 'Ce titre est unique.',
        'similarite_max': meilleure_similarite
    })




from django.shortcuts import render, get_object_or_404
from .models import These, RapportIntermediaire
from django.contrib.auth.decorators import login_required

@login_required
def historique_these(request):
    these = These.objects.filter(utilisateur=request.user).first()
    rapport_inter = RapportIntermediaire.objects.filter(thèse=these).first() if these else None

    context = {
        'these': these,
        'rapport_inter': rapport_inter,
    }
    return render(request, 'presentation/historique.html', {'these': these})



from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden

@login_required
def approuver_rapport_intermediaire(request, id):
    # Vérifiez que l'utilisateur est membre du comité
    if request.user.role != 'comite':
        return HttpResponseForbidden("Vous n'êtes pas autorisé à approuver ce rapport.")

    rapport = get_object_or_404(RapportIntermediaire, id=id)
    rapport.approuve_par_comite = True
    rapport.save()
    return redirect('tableau_theses_comite')  # Redirige vers la page des thèses


@login_required
def approuver_rapport_final(request, rapport_id):
    rapport = get_object_or_404(RapportFinal, id=rapport_id)
    rapport.approuve_par_comite = True
    rapport.save()
    messages.success(request, "Rapport final approuvé.")
    return redirect('tableau_de_bord_comite')  # À adapter



from django.db.models import Count
from .models import Affectation  # assure-toi que c'est importé

def rapport_intermediaire_view(request):
    theses = These.objects.filter(
        statut="Approuvé",
        approuve_par_comite=True
    ).annotate(nb_rapports=Count('rapports_intermediaires')).filter(nb_rapports__gt=0)

    for these in theses:
        # Récupérer le rapport intermédiaire
        rapport = these.rapports_intermediaires.first()
        these.rapport_intermediaire = rapport

        # Ajouter le rapporteur (via Affectation)
        affectation_rapporteur = Affectation.objects.filter(these=these, role='rapporteur').first()
        these.rapporteur = affectation_rapporteur.professeur if affectation_rapporteur else None

    professeurs = Utilisateur.objects.filter(role='professeur')

    query = request.GET.get('q')
    if query:
        theses = [t for t in theses if query.lower() in t.titre.lower()]

    nb_en_attente = sum(1 for t in theses if not hasattr(t, 'rapporteur') or t.rapporteur is None)

    context = {
        'theses': theses,
        'professeurs': professeurs,
        'nb_en_attente': nb_en_attente,
    }
    return render(request, 'presentation/rapport_inter.html', context)

 
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.decorators import login_required
from .models import These, Utilisateur, Affectation, Notification

from django.contrib.auth.decorators import login_required

@login_required
def assigner_rapporteur(request, these_id):
    try:
        if request.method == 'POST':
            rapporteur_id = request.POST.get('rapporteur_id')
            if not rapporteur_id:
                raise ValueError("Aucun rapporteur sélectionné.")

            these = get_object_or_404(These, id=these_id)
            rapporteur = get_object_or_404(Utilisateur, id=rapporteur_id)

            if not Affectation.objects.filter(these=these, professeur=rapporteur, role='rapporteur').exists():
                Affectation.objects.create(
                    professeur=rapporteur,
                    these=these,
                    role='rapporteur'
                )

                # IMPORTANT : mettre à jour le champ rapporteur dans la thèse ET enregistrer
                these.rapporteur = rapporteur
                these.statut_rapport = "Assigné"
                these.save()

                print(f"🚀 Mise à jour: thèse {these.id} - rapporteur assigné à {these.rapporteur.get_full_name()}")

                Notification.objects.create(
                    destinataire=rapporteur,
                    message=f"Vous êtes désigné comme rapporteur pour la thèse : {these.titre}.",
                    type="assignation"
                )

                send_mail(
                    subject="Assignation comme rapporteur",
                    message=(
                        f"Bonjour {rapporteur.get_full_name()},\n\n"
                        f"Vous avez été désigné comme rapporteur pour la thèse suivante :\n\n"
                        f"« {these.titre} ».\n\n"
                        "Merci de consulter votre interface pour plus de détails."
                    ),
                    from_email=settings.EMAIL_HOST_USER,
                    recipient_list=[rapporteur.email],
                    fail_silently=False
                )

                messages.success(request, f"La thèse « {these.titre} » a bien été assignée à {rapporteur.get_full_name()}.")
            else:
                messages.warning(request, f"{rapporteur.get_full_name()} est déjà rapporteur pour cette thèse.")
        
    except Exception as e:
        print("🚨 ERREUR LORS DE L’ASSIGNATION :", str(e))
        messages.error(request, f"Erreur lors de l'assignation : {str(e)}")

    return redirect('rapport_inter')


from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from .models import Affectation, Commentaire, Notification

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Affectation, Commentaire, Notification

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from .models import Affectation, Commentaire, Notification

@login_required
def page_rapporteur(request):
    professeur = request.user
    affectations = Affectation.objects.filter(
        professeur=professeur,
        role='rapporteur',
        decision__isnull=True
    ).order_by('date_ajout')

    total = affectations.count()
    index = int(request.GET.get('index', 0))

    if total == 0:
        affectation = None
    else:
        index = max(0, min(index, total - 1))  # Empêche index négatif ou hors limite
        affectation = affectations[index]

    if request.method == 'POST' and affectation:
        decision = request.POST.get('decision')
        commentaire_text = request.POST.get('commentaire', '').strip()
        grille = request.FILES.get('grille')

        if grille:
            affectation.grille_evaluation = grille
        affectation.decision = decision
        affectation.save()

        if decision in ['avis_mr', 'avis_mjr', 'refuser'] and commentaire_text:
            Commentaire.objects.create(
                these=affectation.these,
                commentaire=commentaire_text,
            )
            Notification.objects.create(
                utilisateur=affectation.these.utilisateur,
                titre="Nouveau commentaire du rapporteur",
                message=f"Votre thèse '{affectation.these.titre}' a reçu un commentaire suite à l'avis '{decision}'.",
                lu=False,
                commentaire=commentaire_text,
            )

        messages.success(request, "Décision enregistrée avec succès.")
        return redirect(f"{request.path}?index={index}")

    context = {
        'affectation': affectation,
        'index': index,
        'total': total,
    }
    return render(request, 'presentation/rapporteur.html', context)





from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from .models import These
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from .models import These

@login_required
def tableau_theses_comite(request):
    try:
        query = request.GET.get('q', '')
        theses = These.objects.all().order_by('id')  # <-- Ajout de l'ordre ici

        if query:
            theses = theses.filter(titre__icontains=query).order_by('id')  # Aussi ici après filtrage

        paginator = Paginator(theses, 5)
        page_number = request.GET.get('page')

        try:
            page_obj = paginator.get_page(page_number)
        except PageNotAnInteger:
            page_obj = paginator.page(1)
        except EmptyPage:
            page_obj = paginator.page(paginator.num_pages)

        professeurs = Utilisateur.objects.filter(role='professeur')
        total_en_attente = theses.filter(statut='En attente').count()

        return render(request, 'presentation/tableau_theses_comite.html', {
            'page_obj': page_obj,
            'total_en_attente': total_en_attente,
            'professeurs': professeurs,
        })
    except Exception as e:
        print(f"Erreur lors de la récupération des thèses : {e}")
        return render(request, 'presentation/erreur.html', {
            'message': f'Une erreur est survenue : {e}'
        })


from django.shortcuts import get_object_or_404
from .models import These
import difflib
import PyPDF2
from docx import Document
from django.http import JsonResponse
import os
from django.conf import settings

# Fonction pour extraire le texte du PDF
def extraire_texte_pdf(fichier_path):
    try:
        with open(fichier_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text = ""
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text
            return text
    except Exception as e:
        print(f"Erreur extraction PDF: {e}")
        return ""

# Fonction pour extraire le texte du fichier Word
def extraire_texte_word(fichier_path):
    try:
        doc = Document(fichier_path)
        text = ""
        for para in doc.paragraphs:
            text += para.text + "\n"
        return text
    except Exception as e:
        print(f"Erreur extraction Word: {e}")
        return ""

# Fonction pour comparer les textes
import difflib
import re

def normaliser_texte(texte):
    texte = texte.lower()  # tout en minuscules
    texte = re.sub(r'\s+', ' ', texte)  # remplace les espaces multiples par un seul
    texte = re.sub(r'[^\w\s]', '', texte)  # supprime ponctuation
    return texte.strip()

def comparer_textes(fichier_1, fichier_2):
    f1_norm = normaliser_texte(fichier_1)
    f2_norm = normaliser_texte(fichier_2)
    return difflib.SequenceMatcher(None, f1_norm, f2_norm).ratio()

def verifier_plagiat_fichier(request, these_id, champ_fichier):
    these = get_object_or_404(These, id=these_id)
    valeur = getattr(these, champ_fichier)

    if hasattr(valeur, 'name'):
        fichiers_a_verifier = [valeur] if valeur else []
    else:
        try:
            fichiers_a_verifier = [f for f in valeur.all() if f and getattr(f, 'name', None)]
        except Exception:
            fichiers_a_verifier = []

    if not fichiers_a_verifier:
        return JsonResponse({"message": f"Aucun fichier {champ_fichier} trouvé.", "plagiat": False})

    for fichier in fichiers_a_verifier:
        if not fichier or not getattr(fichier, 'name', None):
            continue

        if fichier.name.endswith('.pdf'):
            texte_courant = extraire_texte_pdf(fichier.path)
        elif fichier.name.endswith('.docx'):
            texte_courant = extraire_texte_word(fichier.path)
        else:
            continue

        autres_theses = These.objects.exclude(id=these_id)
        for t in autres_theses:
            try:
                autres_valeur = getattr(t, champ_fichier)
                if hasattr(autres_valeur, 'name'):
                    autres_fichiers = [autres_valeur] if autres_valeur else []
                else:
                    try:
                        autres_fichiers = [f for f in autres_valeur.all() if f and getattr(f, 'name', None)]
                    except Exception:
                        autres_fichiers = []

                for autre_fichier in autres_fichiers:
                    if not autre_fichier or not getattr(autre_fichier, 'name', None):
                        continue
                    if autre_fichier.name.endswith('.pdf'):
                        texte_autre = extraire_texte_pdf(autre_fichier.path)
                    elif autre_fichier.name.endswith('.docx'):
                        texte_autre = extraire_texte_word(autre_fichier.path)
                    else:
                        continue

                    similarity_ratio = comparer_textes(texte_courant, texte_autre)
                    print(f"Comparaison {champ_fichier} entre {these.titre} et {t.titre} : {similarity_ratio}")

                    if similarity_ratio >= 0.9:
                        return JsonResponse({
                            "message": "Plagiat détecté ❌",
                            "plagiat": True,
                            "titre": t.titre
                        })
            except Exception as e:
                print(f"Erreur comparaison avec {t.titre}: {e}")

    return JsonResponse({"message": "Aucune similarité détectée ✅", "plagiat": False})



# Puis tes vues deviennent simplement :

def verifier_plagiat(request, these_id):
    return verifier_plagiat_fichier(request, these_id, 'fichier')

def verifier_plagiat_rapport(request, these_id):
    return verifier_plagiat_fichier(request, these_id, 'rapports_intermediaires')




@login_required
def theses_academiques(request):
    theses_academiques = These.objects.filter(domaine='academique')
    return render(request, 'etudiants/theses_academiques.html', {'theses': theses_academiques})

# Commenter la thèse (pour le comité)
@login_required
def commenter_these(request, these_id):
    these = get_object_or_404(These, id=these_id)

    if request.method == 'POST':
        form = CommentaireForm(request.POST)
        if form.is_valid():
            commentaire = form.save(commit=False)
            commentaire.these = these
            commentaire.save()

            # Enregistrer un message à l'étudiant
            message = Message(etudiant=these.utilisateur, contenu=form.cleaned_data['commentaire'])
            message.save()

            # Créer une notification pour l'étudiant
            Notification.objects.create(
                utilisateur=these.utilisateur,
                titre="Nouveau commentaire sur votre thèse",
                message=f"Un commentaire a été ajouté à votre thèse '{these.titre}'.",
                commentaire=form.cleaned_data['commentaire']
            )

            return redirect('tableau_theses_comite')
    else:
        form = CommentaireForm()

    return render(request, 'etudiants/commenter_these.html', {'form': form, 'these': these})


from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from .models import These, Notification

def approuver_these(request, these_id):
    these = get_object_or_404(These, id=these_id)
    
    # Mise à jour du statut de la thèse
    these.statut = 'Approuvé'
    these.approuve_par_comite = True
    these.save()

    # Envoi d'une notification à l'utilisateur (doctorant)
    Notification.objects.create(
        utilisateur=these.utilisateur,
        message=f"Votre thèse intitulée '{these.titre}' a été approuvée par le comité."
    )

    # Message de confirmation pour l'interface d'administration
    messages.success(request, f"La thèse '{these.titre}' a été approuvée avec succès.")
    
    return redirect('tableau_theses_comite')  # Remplace par le nom correct de ta vue ou ton URL




from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import These, Commentaire

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import These, Notification

@csrf_exempt  # à éviter en production, utilise `@login_required` et les protections CSRF
def rejeter_these(request, these_id):
    if request.method == 'POST':
        try:
            these = These.objects.get(id=these_id)
            commentaire = request.POST.get('commentaire', '').strip()

            if not commentaire:
                return JsonResponse({'error': 'Commentaire requis'}, status=400)

            these.statut = 'Rejeté'
            these.commentaire_rejet = commentaire
            these.save()

            # Créer la notification de rejet
            Notification.objects.create(
                utilisateur=these.utilisateur,
                titre="Thèse rejetée",
                message="Votre thèse a été rejetée par le comité.",
                commentaire=commentaire
            )

            return JsonResponse({'message': 'Thèse rejetée avec succès.'})
        except These.DoesNotExist:
            return JsonResponse({'error': 'Thèse introuvable'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Méthode non autorisée'}, status=405)






from django.shortcuts import render
from .models import Notification

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Notification

@login_required
def notifications_view(request):
    notifications = Notification.objects.filter(utilisateur=request.user).order_by('-date_creation')

    # Compter les non lus AVANT de marquer comme lus
    nb_non_lues = notifications.filter(lu=False).count()

    # Marquer les notifications non lues comme lues
    notifications.filter(lu=False).update(lu=True)

    return render(request, 'presentation/notifications.html', {
        'notifications': notifications,
        'nb_non_lues': nb_non_lues,
    })
    
    from gestion.models import Notification
notif = Notification.objects.filter(utilisateur__username='ayan')
print(notif.count())
for n in notif:
    print(n.titre, n.message, n.commentaire)



# dans views.py

    
    
 
from django.shortcuts import render, redirect, get_object_or_404
from .models import These, Affectation, Utilisateur
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail

@login_required
def composition_jury(request):
    theses = These.objects.filter(
        affectation__role='rapporteur',
        affectation__decision__in=['valider', 'avis_sr', 'avis_mr']
    ).distinct()

    # Recherche
    q = request.GET.get('q')
    if q:
        theses = theses.filter(titre__icontains=q)

    theses_list = list(theses)
    index = int(request.GET.get('page', 0))
    these = theses_list[index] if index < len(theses_list) else None

    rapporteurs_map = {}
    affectations_rapporteurs = Affectation.objects.filter(
        role='rapporteur',
        these__in=theses
    ).select_related('professeur', 'these')

    rapporteur_ids = set()
    for aff in affectations_rapporteurs:
        rapporteurs_map[aff.these_id] = aff.professeur
        rapporteur_ids.add(aff.professeur.id)

    professeurs = Utilisateur.objects.filter(role='professeur').exclude(id__in=rapporteur_ids)

    context = {
        'theses': theses,
        'these': these,
        'index': index,
        'professeurs': professeurs,
        'rapporteurs_map': rapporteurs_map,
        'q': q,
        'nb_theses': theses.count()
    }
    return render(request, 'presentation/composition.html', context)


@login_required
def valider_composition(request, these_id):
    if request.method == 'POST':
        these = get_object_or_404(These, id=these_id)

        president_id = request.POST.get('president')
        examinateur_id = request.POST.get('examinateur')
        redacteur_id = request.POST.get('redacteur')

        roles = ['président', 'examinateur', 'rédacteur']
        prof_ids = [president_id, examinateur_id, redacteur_id]

        if len(set(prof_ids)) < 3:
            messages.error(request, "Chaque rôle doit être attribué à un professeur différent.")
            return redirect('composition_jury')

        Affectation.objects.create(these=these, professeur_id=president_id, role='président')
        Affectation.objects.create(these=these, professeur_id=examinateur_id, role='examinateur')
        Affectation.objects.create(these=these, professeur_id=redacteur_id, role='rédacteur')

        # Marquer la thèse comme composée
        these.composition_validee = True
        these.save()

        administration = Utilisateur.objects.filter(role='comite')
        for admin in administration:
            send_mail(
                subject="Nouvelle composition de jury validée",
                message=f"La composition du jury pour la thèse « {these.titre} » a été validée.",
                from_email="",
                recipient_list=[admin.email],
                fail_silently=True
            )

        messages.success(request, "Composition enregistrée avec succès.")
        return redirect('composition_jury')
    
    
    
from django.utils import timezone
from django.shortcuts import render
from .models import Soutenance

def liste_soutenances(request):
    aujourd_hui = timezone.now().date()

    soutenances_a_venir = Soutenance.objects.filter(date_soutenance__gt=aujourd_hui)
    soutenances_en_cours = Soutenance.objects.filter(date_soutenance=aujourd_hui)
    soutenances_passees = Soutenance.objects.filter(date_soutenance__lt=aujourd_hui)

    context = {
        'a_venir': soutenances_a_venir,
        'en_cours': soutenances_en_cours,
        'passees': soutenances_passees,
    }

    return render(request, 'presentation/liste_soutenances.html', context)



from django.contrib.auth import logout
from django.shortcuts import redirect
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def deconnexion_etudiant(request):
    if request.method == "POST":
        logout(request)
        return redirect('connexion')  # Page de connexion pour l'étudiant
    else:
        return redirect('connexion')  # Empêche les accès en GET
    
from django.contrib.auth import logout

def deconnexion_comite(request):
    logout(request)
    return redirect('connexion')  # Redirige vers la page de connexion après la déconnexion


def deconnexion_professeur(request):
    logout(request)
    return redirect('connexion')  # Redirige vers la page de connexion après la déconnexion


