## Dataset

De data die in dit project wordt gebruikt, is afkomstig van [Dutch Parliamentary Voting Dataset](https://dataverse.harvard.edu/dataset.xhtml?persistentId=doi:10.7910/DVN/UXIBNO), met bijgaande [publicate](doi: 10.1057/s41269-017-0042-4).


Deze dataset valt onder de [Creative Commons Attribution 4.0 International License](https://creativecommons.org/licenses/by/4.0/legalcode).

Als je deze dataset gebruikt, verwijs dan naar de oorspronkelijke bron en het bijbehorende Acta Politica-artikel, en zorg ervoor dat je voldoet aan de licentievoorwaarden.

## Licentie

Dit project valt onder de [GNU General Public License (GPL) - Versie 3](LICENSE-GPLv3.txt). Zie het bestand LICENSE-GPLv3.txt voor details.

---

```
CREATE TABLE master_table AS
SELECT 
    voteMatrix.*, 
    categoryList.category,
    categoryList.subcategory,
    metaList.title,
    metaList.subject,
    metaList.date,
    metaList.proposaldate,
    metaList.proposaltype,
    metaList.result,
    metaList.proposalURL,
    metaList.voteURL
FROM (
    SELECT voteMatrix.*, votePerParty.vote_date
    FROM voteMatrix
    JOIN votePerParty ON voteMatrix.id = votePerParty.id
    GROUP BY voteMatrix.id
    ORDER BY votePerParty.vote_date
) AS new_table
JOIN categoryList ON new_table.id = categoryList.id
JOIN metaList ON new_table.id = metaList.id
JOIN votePerParty ON new_table.id = votePerParty.id
GROUP BY new_table.id
ORDER BY votePerParty.vote_date;
```


```
CREATE TABLE new_table AS
SELECT voteMatrix.*, votePerParty.vote_date
FROM voteMatrix
JOIN votePerParty ON voteMatrix.id = votePerParty.id
GROUP BY voteMatrix.id
ORDER BY votePerParty.vote_date;
```


```
CREATE TABLE master_table AS
SELECT 
    new_table.*, 
    categoryList.category,
    categoryList.subcategory,
    metaList.title,
    metaList.subject,
    metaList.date,
    metaList.proposaldate,
    metaList.proposaltype,
    metaList.result,
    metaList.proposalURL,
    metaList.voteURL
FROM new_table
JOIN categoryList ON new_table.id = categoryList.id
JOIN metaList ON new_table.id = metaList.id
JOIN votePerParty ON new_table.id = votePerParty.id
GROUP BY new_table.id
ORDER BY votePerParty.vote_date;
```
