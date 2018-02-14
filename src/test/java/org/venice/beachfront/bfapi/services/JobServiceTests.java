package org.venice.beachfront.bfapi.services;

import org.junit.Before;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.MockitoAnnotations;
import org.venice.beachfront.bfapi.database.dao.JobDao;

public class JobServiceTests {
	@Mock
	private JobDao jobDao;
	@Mock
	private AlgorithmService algorithmService;
	@Mock
	private IABrokerService iaBrokerService;
	@Mock
	private PiazzaService piazzaService;
	@InjectMocks
	private JobService jobService;

	@Before
	public void setup() {
		MockitoAnnotations.initMocks(this);
	}
}
