def get_database_schema():
	table_info = """
        CREATE TABLE "Album" (
	"AlbumId" INTEGER NOT NULL,
	"Title" NVARCHAR(160) NOT NULL,
	"ArtistId" INTEGER NOT NULL,
	PRIMARY KEY ("AlbumId"),
	FOREIGN KEY("ArtistId") REFERENCES "Artist" ("ArtistId")
    )

    /*
    3 rows from Album table:
    AlbumId	Title	ArtistId
    1	For Those About To Rock We Salute You	1
    2	Balls to the Wall	2
    3	Restless and Wild	2
    */


    CREATE TABLE "Artist" (
        "ArtistId" INTEGER NOT NULL,
        "Name" NVARCHAR(120),
        PRIMARY KEY ("ArtistId")
    )

    /*
    3 rows from Artist table:
    ArtistId	Name
    1	AC/DC
    2	Accept
    3	Aerosmith
    */


    CREATE TABLE "Customer" (
        "CustomerId" INTEGER NOT NULL,
        "FirstName" NVARCHAR(40) NOT NULL,
        "LastName" NVARCHAR(20) NOT NULL,
        "Company" NVARCHAR(80),
        "Address" NVARCHAR(70),
        "City" NVARCHAR(40),
        "State" NVARCHAR(40),
        "Country" NVARCHAR(40),
        "PostalCode" NVARCHAR(10),
        "Phone" NVARCHAR(24),
        "Fax" NVARCHAR(24),
        "Email" NVARCHAR(60) NOT NULL,
        "SupportRepId" INTEGER,
        PRIMARY KEY ("CustomerId"),
        FOREIGN KEY("SupportRepId") REFERENCES "Employee" ("EmployeeId")
    )

    /*
    3 rows from Customer table:
    CustomerId	FirstName	LastName	Company	Address	City	State	Country	PostalCode	Phone	Fax	Email	SupportRepId
    1	Luís	Gonçalves	Embraer - Empresa Brasileira de Aeronáutica S.A.	Av. Brigadeiro Faria Lima, 2170	São José dos Campos	SP	Brazil	12227-000	+55 (12) 3923-5555	+55 (12) 3923-5566	luisg@embraer.com.br	3
    2	Leonie	Köhler	None	Theodor-Heuss-Straße 34	Stuttgart	None	Germany	70174	+49 0711 2842222	None	leonekohler@surfeu.de	5
    3	François	Tremblay	None	1498 rue Bélanger	Montréal	QC	Canada	H2G 1A7	+1 (514) 721-4711	None	ftremblay@gmail.com	3
    */


    CREATE TABLE "Employee" (
        "EmployeeId" INTEGER NOT NULL,
        "LastName" NVARCHAR(20) NOT NULL,
        "FirstName" NVARCHAR(20) NOT NULL,
        "Title" NVARCHAR(30),
        "ReportsTo" INTEGER,
        "BirthDate" DATETIME,
        "HireDate" DATETIME,
        "Address" NVARCHAR(70),
        "City" NVARCHAR(40),
        "State" NVARCHAR(40),
        "Country" NVARCHAR(40),
        "PostalCode" NVARCHAR(10),
        "Phone" NVARCHAR(24),
        "Fax" NVARCHAR(24),
        "Email" NVARCHAR(60),
        PRIMARY KEY ("EmployeeId"),
        FOREIGN KEY("ReportsTo") REFERENCES "Employee" ("EmployeeId")
    )

    /*
    3 rows from Employee table:
    EmployeeId	LastName	FirstName	Title	ReportsTo	BirthDate	HireDate	Address	City	State	Country	PostalCode	Phone	Fax	Email
    1	Adams	Andrew	General Manager	None	1962-02-18 00:00:00	2002-08-14 00:00:00	11120 Jasper Ave NW	Edmonton	AB	Canada	T5K 2N1	+1 (780) 428-9482	+1 (780) 428-3457	andrew@chinookcorp.com
    2	Edwards	Nancy	Sales Manager	1	1958-12-08 00:00:00	2002-05-01 00:00:00	825 8 Ave SW	Calgary	AB	Canada	T2P 2T3	+1 (403) 262-3443	+1 (403) 262-3322	nancy@chinookcorp.com
    3	Peacock	Jane	Sales Support Agent	2	1973-08-29 00:00:00	2002-04-01 00:00:00	1111 6 Ave SW	Calgary	AB	Canada	T2P 5M5	+1 (403) 262-3443	+1 (403) 262-6712	jane@chinookcorp.com
    */


    CREATE TABLE "Genre" (
        "GenreId" INTEGER NOT NULL,
        "Name" NVARCHAR(120),
        PRIMARY KEY ("GenreId")
    )

    /*
    3 rows from Genre table:
    GenreId	Name
    1	Rock
    2	Jazz
    3	Metal
    */


    CREATE TABLE "Invoice" (
        "InvoiceId" INTEGER NOT NULL,
        "CustomerId" INTEGER NOT NULL,
        "InvoiceDate" DATETIME NOT NULL,
        "BillingAddress" NVARCHAR(70),
        "BillingCity" NVARCHAR(40),
        "BillingState" NVARCHAR(40),
        "BillingCountry" NVARCHAR(40),
        "BillingPostalCode" NVARCHAR(10),
        "Total" NUMERIC(10, 2) NOT NULL,
        PRIMARY KEY ("InvoiceId"),
        FOREIGN KEY("CustomerId") REFERENCES "Customer" ("CustomerId")
    )

    /*
    3 rows from Invoice table:
    InvoiceId	CustomerId	InvoiceDate	BillingAddress	BillingCity	BillingState	BillingCountry	BillingPostalCode	Total
    1	2	2021-01-01 00:00:00	Theodor-Heuss-Straße 34	Stuttgart	None	Germany	70174	1.98
    2	4	2021-01-02 00:00:00	Ullevålsveien 14	Oslo	None	Norway	0171	3.96
    3	8	2021-01-03 00:00:00	Grétrystraat 63	Brussels	None	Belgium	1000	5.94
    */


    CREATE TABLE "InvoiceLine" (
        "InvoiceLineId" INTEGER NOT NULL,
        "InvoiceId" INTEGER NOT NULL,
        "TrackId" INTEGER NOT NULL,
        "UnitPrice" NUMERIC(10, 2) NOT NULL,
        "Quantity" INTEGER NOT NULL,
        PRIMARY KEY ("InvoiceLineId"),
        FOREIGN KEY("TrackId") REFERENCES "Track" ("TrackId"),
        FOREIGN KEY("InvoiceId") REFERENCES "Invoice" ("InvoiceId")
    )

    /*
    3 rows from InvoiceLine table:
    InvoiceLineId	InvoiceId	TrackId	UnitPrice	Quantity
    1	1	2	0.99	1
    2	1	4	0.99	1
    3	2	6	0.99	1
    */


    CREATE TABLE "MediaType" (
        "MediaTypeId" INTEGER NOT NULL,
        "Name" NVARCHAR(120),
        PRIMARY KEY ("MediaTypeId")
    )

    /*
    3 rows from MediaType table:
    MediaTypeId	Name
    1	MPEG audio file
    2	Protected AAC audio file
    3	Protected MPEG-4 video file
    */


    CREATE TABLE "Playlist" (
        "PlaylistId" INTEGER NOT NULL,
        "Name" NVARCHAR(120),
        PRIMARY KEY ("PlaylistId")
    )

    /*
    3 rows from Playlist table:
    PlaylistId	Name
    1	Music
    2	Movies
    3	TV Shows
    */


    CREATE TABLE "PlaylistTrack" (
        "PlaylistId" INTEGER NOT NULL,
        "TrackId" INTEGER NOT NULL,
        PRIMARY KEY ("PlaylistId", "TrackId"),
        FOREIGN KEY("TrackId") REFERENCES "Track" ("TrackId"),
        FOREIGN KEY("PlaylistId") REFERENCES "Playlist" ("PlaylistId")
    )

    /*
    3 rows from PlaylistTrack table:
    PlaylistId	TrackId
    1	3402
    1	3389
    1	3390
    */


    CREATE TABLE "Track" (
        "TrackId" INTEGER NOT NULL,
        "Name" NVARCHAR(200) NOT NULL,
        "AlbumId" INTEGER,
        "MediaTypeId" INTEGER NOT NULL,
        "GenreId" INTEGER,
        "Composer" NVARCHAR(220),
        "Milliseconds" INTEGER NOT NULL,
        "Bytes" INTEGER,
        "UnitPrice" NUMERIC(10, 2) NOT NULL,
        PRIMARY KEY ("TrackId"),
        FOREIGN KEY("MediaTypeId") REFERENCES "MediaType" ("MediaTypeId"),
        FOREIGN KEY("GenreId") REFERENCES "Genre" ("GenreId"),
        FOREIGN KEY("AlbumId") REFERENCES "Album" ("AlbumId")
    )

    /*
    3 rows from Track table:
    TrackId	Name	AlbumId	MediaTypeId	GenreId	Composer	Milliseconds	Bytes	UnitPrice
    1	For Those About To Rock (We Salute You)	1	1	1	Angus Young, Malcolm Young, Brian Johnson	343719	11170334	0.99
    2	Balls to the Wall	2	2	1	U. Dirkschneider, W. Hoffmann, H. Frank, P. Baltes, S. Kaufmann, G. Hoffmann	342562	5510424	0.99
    3	Fast As a Shark	3	2	1	F. Baltes, S. Kaufman, U. Dirkscneider & W. Hoffman	230619	3990994	0.99
            """

	return table_info
