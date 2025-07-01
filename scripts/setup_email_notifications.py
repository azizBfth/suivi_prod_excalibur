#!/usr/bin/env python3
"""
Script de configuration des notifications email pour le Suivi de Production Excalibur ERP.
"""

import os
import sys
import asyncio
import smtplib
import ssl
from pathlib import Path

# Add the app directory to the Python path
sys.path.append(str(Path(__file__).parent.parent))

from app.services.email_service import EmailService
from app.core.config import get_settings


def print_header():
    """Print setup header."""
    print("=" * 60)
    print("🚀 Configuration des Notifications Email")
    print("   Suivi de Production Excalibur ERP")
    print("=" * 60)
    print()


def print_step(step_num, title):
    """Print step header."""
    print(f"\n📋 Étape {step_num}: {title}")
    print("-" * 40)


def get_user_input(prompt, default=None, required=True):
    """Get user input with optional default."""
    if default:
        full_prompt = f"{prompt} [{default}]: "
    else:
        full_prompt = f"{prompt}: "
    
    while True:
        value = input(full_prompt).strip()
        
        if value:
            return value
        elif default:
            return default
        elif not required:
            return None
        else:
            print("❌ Cette valeur est requise. Veuillez réessayer.")


def validate_email(email):
    """Basic email validation."""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def test_smtp_connection(host, port, user, password):
    """Test SMTP connection."""
    try:
        print(f"🔍 Test de connexion à {host}:{port}...")
        
        with smtplib.SMTP(host, port, timeout=10) as server:
            if port != 25:
                context = ssl.create_default_context()
                server.starttls(context=context)
            
            if user and password:
                server.login(user, password)
        
        print("✅ Connexion SMTP réussie!")
        return True
        
    except Exception as e:
        print(f"❌ Erreur de connexion SMTP: {e}")
        return False


def create_env_file(config):
    """Create or update .env file with email configuration."""
    env_file = Path(".env")
    
    # Read existing .env file if it exists
    existing_config = {}
    if env_file.exists():
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    existing_config[key] = value
    
    # Update with new email configuration
    existing_config.update(config)
    
    # Write updated configuration
    with open(env_file, 'w') as f:
        f.write("# Configuration du Suivi de Production Excalibur ERP\n")
        f.write("# Généré automatiquement par setup_email_notifications.py\n\n")
        
        # Database configuration
        f.write("# Configuration Base de Données\n")
        for key in ['DB_UID', 'DB_PWD', 'DB_HOST', 'DB_SERVER_NAME', 'DB_DATABASE_NAME']:
            if key in existing_config:
                f.write(f"{key}={existing_config[key]}\n")
        f.write("\n")
        
        # Application configuration
        f.write("# Configuration Application\n")
        for key in ['APP_HOST', 'APP_PORT', 'DEBUG', 'LOG_LEVEL']:
            if key in existing_config:
                f.write(f"{key}={existing_config[key]}\n")
        f.write("\n")
        
        # Email configuration
        f.write("# Configuration Email/SMTP\n")
        email_keys = ['SMTP_HOST', 'SMTP_PORT', 'SMTP_USER', 'SMTP_PASSWORD', 
                     'FROM_EMAIL', 'ALERT_EMAIL_RECIPIENTS']
        for key in email_keys:
            if key in existing_config:
                f.write(f"{key}={existing_config[key]}\n")
        f.write("\n")
        
        # Alert configuration
        f.write("# Configuration Alertes\n")
        alert_keys = ['ENABLE_ALERTS', 'ALERT_CHECK_INTERVAL', 'ENABLE_PRODUCTION_NOTIFICATIONS',
                     'DAILY_SUMMARY_TIME', 'OVERDUE_CHECK_INTERVAL', 'URGENT_THRESHOLD_DAYS']
        for key in alert_keys:
            if key in existing_config:
                f.write(f"{key}={existing_config[key]}\n")
        f.write("\n")
        
        # Other configuration
        f.write("# Autres Configurations\n")
        for key, value in existing_config.items():
            if key not in email_keys + alert_keys + ['DB_UID', 'DB_PWD', 'DB_HOST', 'DB_SERVER_NAME', 'DB_DATABASE_NAME', 'APP_HOST', 'APP_PORT', 'DEBUG', 'LOG_LEVEL']:
                f.write(f"{key}={value}\n")
    
    print(f"✅ Fichier .env mis à jour: {env_file.absolute()}")


async def test_email_service(test_email):
    """Test the email service with current configuration."""
    try:
        print(f"📧 Test d'envoi d'email à {test_email}...")
        
        email_service = EmailService()
        
        if not email_service.is_configured():
            print("❌ Service email non configuré")
            return False
        
        result = await email_service.send_test_email(test_email, "basic")
        
        if result["success"]:
            print("✅ Email de test envoyé avec succès!")
            return True
        else:
            print(f"❌ Échec de l'envoi: {result.get('error', 'Erreur inconnue')}")
            return False
            
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
        return False


def main():
    """Main setup function."""
    print_header()
    
    # Step 1: SMTP Configuration
    print_step(1, "Configuration SMTP")
    
    print("Configurons votre serveur SMTP pour l'envoi d'emails.")
    print("Exemples courants:")
    print("  - Gmail: smtp.gmail.com:587")
    print("  - Outlook: smtp.office365.com:587")
    print("  - Serveur local: mail.company.com:25")
    print()
    
    smtp_host = get_user_input("Serveur SMTP (host)")
    smtp_port = get_user_input("Port SMTP", "587")
    smtp_user = get_user_input("Nom d'utilisateur SMTP")
    smtp_password = get_user_input("Mot de passe SMTP")
    from_email = get_user_input("Adresse email expéditeur", smtp_user)
    
    # Step 2: Test SMTP Connection
    print_step(2, "Test de Connexion SMTP")
    
    if not test_smtp_connection(smtp_host, int(smtp_port), smtp_user, smtp_password):
        print("\n❌ La connexion SMTP a échoué.")
        print("Veuillez vérifier vos paramètres et réessayer.")
        return False
    
    # Step 3: Recipients Configuration
    print_step(3, "Configuration des Destinataires")
    
    print("Configurons les destinataires des notifications.")
    recipients = []
    
    while True:
        email = get_user_input(f"Adresse email destinataire #{len(recipients) + 1}", required=len(recipients) == 0)
        
        if not email:
            break
        
        if validate_email(email):
            recipients.append(email)
            print(f"✅ {email} ajouté")
        else:
            print(f"❌ {email} n'est pas une adresse email valide")
        
        if len(recipients) > 0:
            more = get_user_input("Ajouter un autre destinataire? (o/N)", "n", False)
            if more.lower() not in ['o', 'oui', 'y', 'yes']:
                break
    
    # Step 4: Alert Configuration
    print_step(4, "Configuration des Alertes")
    
    enable_alerts = get_user_input("Activer les alertes automatiques? (O/n)", "o")
    alert_interval = get_user_input("Intervalle de vérification des alertes (secondes)", "1800")
    
    enable_production = get_user_input("Activer les notifications de production? (O/n)", "o")
    daily_summary_time = get_user_input("Heure d'envoi du résumé quotidien (HH:MM)", "08:00")
    overdue_interval = get_user_input("Intervalle de vérification des retards (secondes)", "1800")
    urgent_threshold = get_user_input("Seuil d'urgence (jours avant échéance)", "2")
    
    # Step 5: Create Configuration
    print_step(5, "Création de la Configuration")
    
    config = {
        'SMTP_HOST': smtp_host,
        'SMTP_PORT': smtp_port,
        'SMTP_USER': smtp_user,
        'SMTP_PASSWORD': smtp_password,
        'FROM_EMAIL': from_email,
        'ALERT_EMAIL_RECIPIENTS': ','.join(recipients),
        'ENABLE_ALERTS': 'true' if enable_alerts.lower() in ['o', 'oui', 'y', 'yes'] else 'false',
        'ALERT_CHECK_INTERVAL': alert_interval,
        'ENABLE_PRODUCTION_NOTIFICATIONS': 'true' if enable_production.lower() in ['o', 'oui', 'y', 'yes'] else 'false',
        'DAILY_SUMMARY_TIME': daily_summary_time,
        'OVERDUE_CHECK_INTERVAL': overdue_interval,
        'URGENT_THRESHOLD_DAYS': urgent_threshold
    }
    
    create_env_file(config)
    
    # Step 6: Test Email Service
    print_step(6, "Test du Service Email")
    
    test_email = get_user_input("Adresse email pour le test", recipients[0] if recipients else None)
    
    if test_email and validate_email(test_email):
        # Reload environment variables
        os.environ.update(config)
        
        success = asyncio.run(test_email_service(test_email))
        
        if success:
            print("\n🎉 Configuration terminée avec succès!")
            print("\nPour démarrer l'application:")
            print("  python main.py")
            print("\nPour accéder au dashboard:")
            print("  http://0.0.0.0:80")
            print("\nPour tester les notifications:")
            print("  http://0.0.0.0:80/docs (API Swagger)")
        else:
            print("\n⚠️  Configuration sauvegardée mais le test d'email a échoué.")
            print("Vérifiez les logs de l'application pour plus de détails.")
    else:
        print("\n✅ Configuration sauvegardée.")
        print("Vous pouvez tester les emails plus tard via l'API.")
    
    return True


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n❌ Configuration interrompue par l'utilisateur.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Erreur inattendue: {e}")
        sys.exit(1)
