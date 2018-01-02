package org.venice.beachfront.bfapi.services;

import java.util.concurrent.CompletableFuture;

import org.venice.beachfront.bfapi.model.Scene;

public interface IABrokerService {
	public String activateScene(Scene scene, String planetApiKey);
	public Scene getScene(String sceneId, String planetApiKey, boolean withTides);
	
	public CompletableFuture<String> asyncActivateScene(Scene scene, String planetApiKey);
}
