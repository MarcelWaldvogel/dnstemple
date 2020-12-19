$ADDRESS	mail	mail

@		MX	10 mail.example.com.
		TXT	"v=spf1 mx ~all"
autodiscover	CNAME	mail
autoconfig	CNAME	mail
smtp		CNAME	mail
imap		CNAME	mail
dkim._domainkey	TXT	"v=DKIM1;k=rsa;t=s;s=email;p={dkimkey}"
_dmarc		TXT	"v=DMARC1; p=none; rua=mailto:dkim@example.com; fo=1:d:s"
