# Water-Tracker

## Connection aux API
### Hubeau

**Piézométrie**
Les relevés piézométriques sont effectué dans certaines stations de mesures. La liste des station est obtensible via des requêtes à l'url suivant : `https://hubeau.eaufrance.fr/api/v1/niveaux_nappes/stations`.
Chaque station est identifiée par un code national. A l'aide de ce code (`code_bss`), il est possible d'obtenir les relevés piézométriques d'une station de mesure, via des requêtes à l'url suivant : `https://hubeau.eaufrance.fr/api/v1/niveaux_nappes/chroniques`. Il est nécessaire de fournir une valeur pour le paramètre `code_bss` lors d'une requête à cette API.  