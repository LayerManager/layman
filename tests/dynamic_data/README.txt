Poznámky:
Asynchronní chyba pro nás není nijak specifická, testujeme ji assertovací metodou.
Smazaná publikace pro nás není nijak specifická, testujeme ji assertovací metodou.
Mezistavy můžeme kontrolovat pomocí jiné check_fn ve volání publish_workspace_publication.
Jedna metoda ověřuje hodnoty v get_publication_info, všechny ostatní testy věří hodnotám z get_publication_info.

Pravidla:
1. Každá položka v hodnotách PUBLICATIONS obsahuje 'action'
1. 'final_asserts' se většinou pouštějí až když neběží žádný asynchronní krok (publikace je ve stavu COMPLETE nebo INCOMPLETE), záleží na check_fn
