# Installation et configuration de AioMda

## Présentation :

le module **AioMda** se situe entre **Postfix** et **Cyrus IMAP** :


1) **Postfix** va envoyer le mail vers le démon **AioSmtpd** qui écoute en local sur le port par défaut **9025**.
2) **AioMda** fait le traitement si besoin (ex: absence).
3) Ensuite **AioMda** envoi le mail à **Cyrus** sur le démon **lmtpd**.

## Prérequis :

- python34-aiosmtpd : installe **python3.4** + la librairie **Aiosmtpd**
- python34-pip : installation du gestionnaire de module python **pip**
- pip3.4 install --upgrade pip : mise à jour de **pip**
- pip3.4 install ldap3 : installation de **ldap3** pour **python3.4**


## Configuration :
Cyrus /etc/cyrus.conf:

    lmtpunix      cmd="lmtpd" listen="/var/lib/imap/socket/lmtp" prefork=1


Postfix /etc/postfix/main.cf:

    mailbox_transport=lmtp:127.0.0.1:9025

Aiosmtpd :


## Utilisation :


1) configuration du module :

voir le fichier **example.conf**
