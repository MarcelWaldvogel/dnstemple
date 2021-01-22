$ORIGIN		{_domain}
$TTL		86400
;
; Assuming we use Knot DNS with `zonefile-load: difference-no-serial`, the
; serial number can be held constant using `config.serial: 1`; otherwise use
; the `_serial` variable. Also simplifies file difference detection.
;
; If you prefer the source file to keep track of the serial, setting
; `config.serial` to `unixtime` (in case you do not have more than one change
; per second) or `online` (to have `YYMMDDxx`-style serials with comparison
; against the live zone; slow)
@		SOA	(ns1.example.com. hostmaster.example.com. {_serial} 3600 1800 2419200 300)
		NS	ns1.example.com.
		NS	ns2.example.com.
		CAA	0 issue "{ca}"
