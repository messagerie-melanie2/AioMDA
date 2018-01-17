from datetime import datetime
# ^[0-9]{2};{Version};(ALL|IN|OUT);[0-9]{14}Z;[0-9]{14}Z;[dhms][1-9][0-9]*;{repetitivite};[^;]*;[^;]*$
# 1. numéro d'ordre : [0-9]{2} => En premier pour continuer à bénéficier du tri
# 2. version : numéro incrémental ou x.y.z ou autre chose qui sera
# renseigné par nos outils à la pose et qui sera consommé par le
# middleware => Permettant au middleware d'identifier l'ordre des
# valeurs venant ensuite
# 3. périmètre : ALL, IN, OUT, etc.
# 4. date début : Timestamp
# 5. date fin : Timestamp
# 6. délai entre 2 message : [dhms][1-9][0-9]*
# 7. répétitivité => Nouveau paramètre intégrant la problématique de répétitivité.
# 8. sujet : [^;]*
# 9. corps du message : [^;]*
#
#

# je pose un temps partiel du 1er janvier 2018 au 31 décembre 2018 pour une absence un mercredi sur 2.
# 01;1;IN;20180101000000Z;20181231235959Z;d7;* * * * 3 1,3;Auto: %s; Je suis absent ce jour. Si votre demande est urgente, veuillez contacter l'équipe à l'adresse

# re_rules = re.compile(r'^(\d+)~ (RAIN:(.*?))(( DDEB:(\d{8}))?( DFIN:(\d{8}))?( DSVT:(\d?))?)?( FREQ:(\d*))?( TEXTE:(.*?)?)$', re.DOTALL)

# r = re_rules.findall("01;1;IN;20180101000000Z;20181231235959Z;d7;* * * * 3 1,3;Auto: %s; Je suis absent ce jour. Si votre demande est urgente, veuillez contacter l'équipe à l'adresse")

class Recurrence:
    """ Gestion du champ récurrence pour mceVacation
    * * * * * * * => minute, heure, jour, mois, jour de la semaine, num semaine

    * minute : 0-59
    * heure : 0-23
    * jours : 1-31
    * mois : 1-12
    * jour de la semaines : 0-7
    * semaine : 0-3
    """

    def __init__(self,rec):
        maintenant = datetime.now()
        num_semaine_mois = int(maintenant.isocalendar()[1]) - int(datetime(maintenant.year,maintenant.month,1).isocalendar()[1])
        self.rec = rec
        self.aujourdhui = [
            ("minute",maintenant.minute,59),
            ("heure",maintenant.hour,23),
            ("jour",maintenant.day,31),
            ("mois",maintenant.month,12),
            ("jour semaine",maintenant.isoweekday(),7), # lundi 1 dimanche 7
            ("num semaine mois",num_semaine_mois,4)
            ]

    def isMaintenant(self):
        val = self.rec.split(' ')
        try:
            for g in range(6):
                self.analyse_champ(val[g],self.aujourdhui[g])
        except Exception as err:
            x, y = err.args
            print("{} : {}".format(x,y))
            return False
        else:
            return True

    def info(self):
        print("variable de départ : {}".format(self.rec))
        print("date d'aujourd'hui : {}".format(self.aujourdhui))

    def analyse_champ(self,chaine,comp):
        if chaine != '*':
            valeurs_chaine = chaine.split(',')
            n=0
            t=0
            nb = len(valeurs_chaine)
            pas = 1
            try:
                while n < nb:
                    tmp = valeurs_chaine[t].split('/')
                    if "/" in valeurs_chaine[t]:
                        pas = int(tmp[-1])

                    if "-" in tmp[0]:
                        interval = tmp[0].split('-')
                        del valeurs_chaine[t]
                        for i in range(int(interval[0]),int(interval[1])+1,pas):
                            valeurs_chaine.append("{}".format(i))
                    elif "*" in tmp[0]:
                        for i in range(0,int(comp[2])+1,pas):
                            valeurs_chaine.append("{}".format(i))
                    else: t=t+1
                    n=n+1
            except ValueError as err:
                raise Exception('Mauvaise valeur', "'{}' n'est pas au bon format : {}".format(
                        comp[0],chaine))
            valeurs_entier = [int(x) for x in valeurs_chaine]
            valeurs_entier.sort()
            print("MIN : {} | MAX : {}".format(valeurs_entier[0],valeurs_entier[-1]))
            if valeurs_entier[0] < 0 or valeurs_entier[-1] > comp[2]:
                raise Exception('Mauvaise valeur', "{} -> MIN (0) : {} | MAX ({}) : {}".format(
                        comp[0],valeurs_entier[0],comp[2],valeurs_entier[-1]))
            if comp[1] not in valeurs_entier:
                raise Exception('Pas applicable', "{} -> {} -> {}".format(comp[0],comp[1],valeurs_entier))
