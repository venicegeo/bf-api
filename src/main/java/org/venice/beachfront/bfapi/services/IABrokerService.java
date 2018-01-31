package org.venice.beachfront.bfapi.services;

import java.util.concurrent.CompletableFuture;

import org.springframework.stereotype.Service;
import org.venice.beachfront.bfapi.model.Scene;

@Service
public class IABrokerService {
	public String activateScene(Scene scene, String planetApiKey) {
		return null; // TODO
	}

	public Scene getScene(String sceneId, String planetApiKey, boolean withTides) {
		return null; // TODO
	}

	public CompletableFuture<String> asyncActivateScene(Scene scene, String planetApiKey) {
		return null; // TODO
	}
}
