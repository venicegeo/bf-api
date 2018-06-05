package org.venice.beachfront.bfapi.config;

import org.apache.http.HeaderElement;
import org.apache.http.HeaderElementIterator;
import org.apache.http.HttpResponse;
import org.apache.http.conn.ConnectionKeepAliveStrategy;
import org.apache.http.message.BasicHeaderElementIterator;
import org.apache.http.protocol.HTTP;
import org.apache.http.protocol.HttpContext;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Configuration;

@Configuration
public class BaseAuthenticationConfig {

	@Value("${http.keep.alive.duration.seconds}")
	private int httpKeepAliveDurationSeconds;

	/**
	 * Defines a keep-alive strategy for requests that do not provide a proper timeout value. This will avoid a case
	 * where keep-alive is set to permanent (when the header is missing) in cases where this application's environment
	 * will not allow for permanent connections.
	 */
	protected ConnectionKeepAliveStrategy getKeepAliveStrategy() {
		// Returns the keep alive duration, in milliseconds
		return (HttpResponse response, HttpContext context) -> {
			HeaderElementIterator it = new BasicHeaderElementIterator(response.headerIterator(HTTP.CONN_KEEP_ALIVE));
			while (it.hasNext()) {
				final HeaderElement headerElement = it.nextElement();
				final String param = headerElement.getName();
				final String value = headerElement.getValue();
				if (value != null && param.equalsIgnoreCase("timeout")) {
					return Long.parseLong(value) * 1000;
				}
			}
			return httpKeepAliveDurationSeconds * 1000;
		};
	}
}