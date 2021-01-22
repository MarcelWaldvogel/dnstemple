$ORIGIN		{_domain}
$TTL		86400
; Assuming we use Knot DNS with `zonefile-load: difference-no-serial`, we can
; keep the serial here constant; otherwise use the `_serial` variable.
; Also simplifies file difference detection.
@		SOA	(ns1.example.com. hostmaster.example.com. 1 3600 1800 2419200 300)
		NS	ns1.example.com.
		NS	ns2.example.com.
		CAA	0 issue "{ca}"
