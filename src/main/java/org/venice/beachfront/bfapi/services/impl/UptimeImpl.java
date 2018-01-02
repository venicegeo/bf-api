package org.venice.beachfront.bfapi.services.impl;

import org.springframework.stereotype.Service;
import org.venice.beachfront.bfapi.services.Uptime;

@Service
public class UptimeImpl implements Uptime {
	private long startTimeMillis = System.currentTimeMillis();
	
	@Override
	public double getUptimeSeconds() {
		long uptimeMillis = System.currentTimeMillis() - this.startTimeMillis;
		return ((double)uptimeMillis) / 1000;
	}

}
