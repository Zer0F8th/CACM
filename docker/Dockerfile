FROM alpine:3.20

RUN apk add --no-cache net-snmp net-snmp-tools

COPY snmpd.conf /etc/snmp/snmpd.conf

EXPOSE 161/udp

# Run snmpd in foreground, listening on all interfaces
CMD ["snmpd", "-f", "-Lo", "-C", "-c", "/etc/snmp/snmpd.conf"]
