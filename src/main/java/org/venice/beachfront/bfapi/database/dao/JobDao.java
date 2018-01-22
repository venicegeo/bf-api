package org.venice.beachfront.bfapi.database.dao;

import javax.transaction.Transactional;

import org.springframework.data.repository.CrudRepository;
import org.venice.beachfront.bfapi.model.Job;

@Transactional
public interface JobDao extends CrudRepository<Job, Long> {
}
