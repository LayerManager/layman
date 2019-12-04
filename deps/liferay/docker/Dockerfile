FROM liferay/portal:7.1.3-ga4

# https://github.com/docker/compose/issues/3270#issuecomment-206214034
USER root
RUN   mkdir -p /etc/liferay/tmp
RUN   chown liferay:liferay /etc/liferay/tmp

USER liferay
