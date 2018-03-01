package org.venice.beachfront.bfapi.database.dao;

import javax.transaction.Transactional;

import org.springframework.data.repository.CrudRepository;
import org.venice.beachfront.bfapi.model.Scene;

@Transactional
public interface SceneDao extends CrudRepository<Scene, String> {
	Scene findBySceneId(String SceneId);
}
