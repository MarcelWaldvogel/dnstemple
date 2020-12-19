# DNS Temple • A DNS TEMPLating Engine

Maintaining several domains ("zones") can be a hassle. Often, a lot of basic
information is shared between domains (name, mail or web servers, anti-spam
configuration etc.). `CNAME`s can help to keep information in a single
location, but are not compatible e.g. with information stored at the apex (the
domain name itelf), and thus are of limited or no use for the above-mentioned
shared information. When creating a new zone, a previous zone can be copied;
however, if later things have to change for these domains, a lot of manual
labor is required, prone to errors. DNS Temple tries to simplify this.

# Motivating example

## Traditional setup

Main site:
```bind
$ORIGIN		example.com.
$TTL		86400
@		SOA	(ns1.example.com. hostmaster.example.com. 2020121901 3600 1800 2419200 300)
		NS	ns1.example.com.
		NS	ns2.example.com.
		MX	10 mail.example.com.
		TXT	"v=spf1 mx ~all"
		TXT	"google-site-verification=zeePiegahyeiVoh4SheiK5ootees2Uy4DaiKawoh"
		A	192.0.2.80
		AAAA	2001:db8:1234:5678::80
		CAA	0 issue "letsencrypt.org"
ns1		A	203.0.113.53
		AAAA	2001:db8:1:2::53
ns2		A	198.51.100.53
		AAAA	2001:db8:3:4::53
# Web
www		A	192.0.2.80
		AAAA	2001:db8:1234:5678::80
# Mail
autodiscover	CNAME	mail
autoconfig	CNAME	mail
mail		A	192.0.2.25
		AAAA	2001:db8:1234:5678::25
smtp		CNAME	mail
imap		CNAME	mail
dkim._domainkey	TXT	"v=DKIM1;k=rsa;t=s;s=email;p=MII..."
_dmarc		TXT	"v=DMARC1; p=none; rua=mailto:dkim@example.com; fo=1:d:s"
# Cloud
cloud		A	192.0.2.90
		AAAA	2001:db8:1234:5678::90
```

One of many secondary sites:
```bind
$ORIGIN		example.ch.
$TTL		86400
@		SOA	(ns1.example.com. hostmaster.example.com. 2020121901 3600 1800 2419200 300)
		NS	ns1.example.com.
		NS	ns2.example.com.
		MX	10 mail.example.com.
		TXT	"v=spf1 mx ~all"
		TXT	"google-site-verification=isei8oox1gahc7oox1ezith9eith2ki8aigh9aiD"
		A	192.0.2.80
		AAAA	2001:db8:1234:5678::80
		CAA	0 issue "letsencrypt.org"
# Web
www		A	192.0.2.80
		AAAA	2001:db8:1234:5678::80
# Mail
autodiscover	CNAME	mail
autoconfig	CNAME	mail
mail		A	192.0.2.25
		AAAA	2001:db8:1234:5678::25
smtp		CNAME	mail
imap		CNAME	mail
dkim._domainkey	TXT	"v=DKIM1;k=rsa;t=s;s=email;p=MII..."
_dmarc		TXT	"v=DMARC1; p=none; rua=mailto:dkim@example.com; fo=1:d:s"
```

The `mail`, `_dkim`, and `www` entries could be changed to `CNAME`s and the SPF entry
could use `include:`, but many problems would still remain, such as:

1. Changing the address of the web server would require changing all the files anyway.
1. Changing the list of name servers, certificate authorities, or mail servers
   cause modification of every file.
1. `SOA` serials need to be incremented carefully to avoid hard-to-diagnose problems.
1. Adding an additional service, such as a secondary mail server, CardDAV,
   CalDAV, or XMPP would require touching every file.
1. Over time, files will diverge, due to some services (such as cloud)
   appearing in some zones only or authentication entries (such as
   `google-site-verification`, maybe `_domainkey`) differing between domains.
1. You will lose oversight because of all the clutter and differences.


## Configuration with DNS Temple

Create a central configuration where shared information is collected:
```yaml
addresses:
	ns1:	203.0.113.53	2001:db8:1:2::53
	ns2:	198.51.100.53	2001:db8:3:4::53
	mail:	192.0.2.25	2001:db8:1234:5678::25
	web:	192.0.2.80	2001:db8:1234:5678::80
	cloud:	192.0.2.90	2001:db8:1234:5678::90
variables:
	ca:	letsencrypt.org
	dkimkey: MII...
```

Create a set of templates using `{variable}` references, `$ADDRESS` explosions
(expanding dynamically to a set of `A` and `AAAA` records), and `$INCLUDE`s:

- `header.t`:
```bind
$ORIGIN		{zone}
$TTL		86400
@		SOA	(ns1.example.com. hostmaster.example.com. {serial} 3600 1800 2419200 300)
		NS	ns1.example.com.
		NS	ns2.example.com.
		CAA	0 issue "{ca}"
```

- `mail.t`:
```bind
$ADDRESS	mail	mail

@		MX	10 mail.example.com.
		TXT	"v=spf1 mx ~all"
autodiscover	CNAME	mail
autoconfig	CNAME	mail
smtp		CNAME	mail
imap		CNAME	mail
dkim._domainkey	TXT	"v=DKIM1;k=rsa;t=s;s=email;p={dkimkey}"
_dmarc		TXT	"v=DMARC1; p=none; rua=mailto:dkim@example.com; fo=1:d:s"
```

- `web.t`:
```bind
$ADDRESS	web	@
$ADDRESS	web	www
```

- `common.t`:
```bind
$INCLUDE	header.t	zone={zone}
$INCLUDE	mail.t
$INCLUDE	web.t
```

These configuration templates will be shared among the zones, resulting in much more compact files:

```bind
$INCLUDE	common.t	zone=example.com.
$ADDRESS	ns1	ns1
$ADDRESS	ns2	ns2
$ADDRESS	cloud	cloud
@		TXT	"google-site-verification=zeePiegahyeiVoh4SheiK5ootees2Uy4DaiKawoh"
```

```bind
$INCLUDE	common.t	zone=example.ch.
$ADDRESS	ns1	ns1
$ADDRESS	ns2	ns2
$ADDRESS	cloud	cloud
@		TXT	"google-site-verification=isei8oox1gahc7oox1ezith9eith2ki8aigh9aiD"
```
